import enum
from uuid import uuid4

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text, Table
)
from sqlalchemy.dialects.mysql import CHAR, INTEGER, JSON, TINYINT, DECIMAL, BIGINT
from sqlalchemy.orm import declarative_base, relationship

from malppot.utils.datetime_utils import now_kst

Base = declarative_base()


class Difficulty(str, enum.Enum):
    EASY = "EASY"
    NORMAL = "NORMAL"
    HARD = "HARD"


class PracticeWordErrorType(str, enum.Enum):
    OMISSION = "Omission"
    INSERTION = "Insertion"
    MISPRONUNCIATION = "Mispronunciation"
    NONE = "None"


class VideoLogStatus(str, enum.Enum):
    pending = "pending"
    done = "done"
    failed = "failed"


class PracticeWordPosition(str, enum.Enum):
    CHOSUNG = "초성"
    JONGSUNG = "종성"


stage_words_link = Table(
    'stage_words_link', Base.metadata,
    Column('stage_id', Integer, ForeignKey('stage_info.stage_id', ondelete="CASCADE"), primary_key=True),
    Column('game_word_id', BIGINT(unsigned=True), ForeignKey('game_words.id', ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = 'users'
    user_idx = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    google_id = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))
    profile_image_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=now_kst)
    last_login_at = Column(DateTime(timezone=True), default=now_kst, onupdate=now_kst)
    practice_streak = Column(INTEGER(unsigned=True), default=0)
    total_practice_count = Column(INTEGER(unsigned=True), default=0)
    current_average_accuracy = Column(Float, default=0.0)
    previous_average_accuracy = Column(Float, default=0.0)

    practice_sessions = relationship("PracticeSession", back_populates="user")
    jamo_statistics = relationship("JamoStatistic", back_populates="user")
    practice_words = relationship("PracticeWord", back_populates="user")


class GameType(Base):
    __tablename__ = 'game_types'
    game_type_idx = Column(CHAR(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    practice_sessions = relationship("PracticeSession", back_populates="game_type")


class Word(Base):
    __tablename__ = 'words'
    word_idx = Column(CHAR(36), primary_key=True)
    text = Column(String(100), nullable=False)
    pronunciation = Column(Text)

    practice_words = relationship("PracticeWord", back_populates="word")


class PracticeSession(Base):
    __tablename__ = 'practice_sessions'
    session_idx = Column(CHAR(36), primary_key=True)
    user_idx = Column(INTEGER(unsigned=True), ForeignKey('users.user_idx'), nullable=False)
    game_type_idx = Column(CHAR(36), ForeignKey('game_types.game_type_idx'))
    sentence_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=now_kst)
    accuracy_score = Column(Float)
    fluency_score = Column(Float)
    completeness_score = Column(Float)
    original_text = Column(Text)

    user = relationship("User", back_populates="practice_sessions")
    game_type = relationship("GameType", back_populates="practice_sessions")
    practice_words = relationship("PracticeWord", back_populates="practice_session")


class PracticeWord(Base):
    __tablename__ = 'practice_words'
    practice_word_idx = Column(CHAR(36), primary_key=True)
    session_idx = Column(CHAR(36), ForeignKey('practice_sessions.session_idx'), nullable=False)
    word_idx = Column(CHAR(36), ForeignKey('words.word_idx'))
    spoken_text = Column(Text)
    average_score = Column(Float)
    error_type = Column(
        Enum(
            'Omission',
            'Insertion',
            'Mispronunciation',
            'None',
            name='practiceworderrortype'
        ),
        default='None'
    )
    user_idx = Column(INTEGER(unsigned=True), ForeignKey('users.user_idx'))

    practice_session = relationship("PracticeSession", back_populates="practice_words")
    word = relationship("Word", back_populates="practice_words")
    user = relationship("User", back_populates="practice_words")
    pronunciation_scores = relationship("PronunciationScore", back_populates="practice_word")


class PronunciationScore(Base):
    __tablename__ = 'pronunciation_scores'
    score_idx = Column(CHAR(36), primary_key=True)
    practice_word_idx = Column(CHAR(36), ForeignKey('practice_words.practice_word_idx'), nullable=False)
    jamo_char = Column(String(10))
    score = Column(Float)
    jamo_position = Column(
        Enum(
            "초성",
            "종성"
        ), nullable=True)
    practice_word = relationship("PracticeWord")


class Syllable(Base):
    __tablename__ = 'syllables'
    syllable_char = Column(String(10), primary_key=True)
    tongue_url = Column(JSON, nullable=False)
    lips_url = Column(JSON, nullable=False)
    gpt_tip = Column(Text, nullable=True)


class JamoStatistic(Base):
    __tablename__ = 'jamo_statistics'
    user_idx = Column(INTEGER(unsigned=True), ForeignKey('users.user_idx'), primary_key=True)
    jamo_char = Column(String(10), primary_key=True)
    attempt_count = Column(Integer, default=0)
    total_score = Column(Float, default=0.0)

    user = relationship("User", back_populates="jamo_statistics")


class RecommendationsWords(Base):
    __tablename__ = 'recommendation_words'

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid4()))
    jamo_initial = Column(String(10), nullable=False, index=True)
    words = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_kst, index=True)


class StageInfo(Base):
    __tablename__ = "stage_info"
    stage_id = Column(Integer, primary_key=True)
    level = Column(Integer, nullable=False)
    difficulty = Column(Enum(Difficulty), nullable=False)
    goal_value = Column(Integer, nullable=False)
    speed = Column(DECIMAL(3, 1), nullable=False)
    interval_ms = Column(Integer, nullable=False)
    lives = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=now_kst)

    words = relationship(
        "GameWord",
        secondary=stage_words_link,
        back_populates="stages"
    )


class UserStageProgress(Base):
    __tablename__ = "user_stage_progress"

    user_idx = Column(INTEGER(unsigned=True), ForeignKey("users.user_idx"), primary_key=True)
    stage_id = Column(Integer, ForeignKey("stage_info.stage_id"), primary_key=True)
    cleared = Column(TINYINT(1), default=0)
    cleared_at = Column(DateTime(timezone=True), nullable=True)

    stage = relationship("StageInfo", backref="progresses")
    user = relationship("User", backref="stage_progress")


class EndlessScores(Base):
    __tablename__ = "endless_scores"

    user_idx = Column(INTEGER(unsigned=True), ForeignKey("users.user_idx"), primary_key=True)
    best_score = Column(Integer, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_kst, onupdate=now_kst)

    user = relationship("User", backref="endless_score")


class GameWord(Base):
    __tablename__ = "game_words"
    id = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    word = Column(String(255), nullable=False, unique=True)
    image_url = Column(String(1024))
    created_at = Column(DateTime(timezone=True), default=now_kst)
    stages = relationship(
        "StageInfo",
        secondary="stage_words_link",
        back_populates="words"
    )
