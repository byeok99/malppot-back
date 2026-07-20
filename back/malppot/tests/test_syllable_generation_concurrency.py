import asyncio
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from malppot.domain.models import Base, Syllable
from malppot.domain.speech.service import SpeechService


class _TestDb:
    def __init__(self):
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_session(self):
        return self.SessionLocal()


class _CountingGpt:
    def __init__(self):
        self.calls = 0

    async def ask(self, _prompt: str) -> str:
        self.calls += 1
        await asyncio.sleep(0.01)
        return "tip"


class _BusyRedis:
    async def set(self, *_args, **_kwargs):
        return False

    async def eval(self, *_args, **_kwargs):
        return 0


def _make_service(db: _TestDb, gpt: _CountingGpt | None = None) -> SpeechService:
    service = object.__new__(SpeechService)
    service.db = db
    service.gpt_service = gpt or _CountingGpt()
    service._syllable_locks = {}
    service._syllable_locks_guard = asyncio.Lock()
    service._redis = None
    service._redis_lock_ttl = 120
    service._redis_lock_wait_timeout = 0.01
    return service


class SyllableGenerationConcurrencyTest(unittest.TestCase):
    def test_ensure_syllable_row_creates_empty_json_defaults(self):
        db = _TestDb()
        service = _make_service(db)
        session = db.get_session()
        try:
            row = service._ensure_syllable_row(session, "가")
            session.commit()

            self.assertEqual(row.syllable_char, "가")
            self.assertEqual(row.tongue_url, [])
            self.assertEqual(row.lips_url, [])
        finally:
            session.close()

    def test_concurrent_gpt_tip_population_uses_single_external_call(self):
        async def run_test():
            db = _TestDb()
            gpt = _CountingGpt()
            service = _make_service(db, gpt)

            await asyncio.gather(
                service._populate_syllable_gpt_tips(["가"]),
                service._populate_syllable_gpt_tips(["가"]),
            )

            session = db.get_session()
            try:
                rows = session.query(Syllable).filter_by(syllable_char="가").all()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0].gpt_tip, "tip")
                self.assertEqual(rows[0].tongue_url, [])
                self.assertEqual(rows[0].lips_url, [])
                self.assertEqual(gpt.calls, 1)
            finally:
                session.close()

        asyncio.run(run_test())

    def test_busy_redis_lock_rechecks_without_external_call(self):
        async def run_test():
            db = _TestDb()
            gpt = _CountingGpt()
            service = _make_service(db, gpt)
            service._redis = _BusyRedis()

            await service._populate_syllable_gpt_tips(["가"])

            self.assertEqual(gpt.calls, 0)
            session = db.get_session()
            try:
                rows = session.query(Syllable).filter_by(syllable_char="가").all()
                self.assertEqual(len(rows), 0)
            finally:
                session.close()

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
