import enum
from uuid import uuid4

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.mysql import CHAR, INTEGER, JSON, TINYINT, DECIMAL
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

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
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


class PracticeWordPosition(str, enum.Enum):
    CHOSUNG = "초성"
    JONGSUNG = "종성"


class User(Base):
    __tablename__ = 'users'
    user_idx = Column(INTEGER(unsigned=True), primary_key=True, autoincrement=True)
    google_id = Column(String(50), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100))
    profile_image_url = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    last_login_at = Column(DateTime, default=func.now(), onupdate=func.now())
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
    representative_video_id = Column(CHAR(36), ForeignKey('video_logs.video_id'))

    representative_video = relationship("VideoLog")
    practice_words = relationship("PracticeWord", back_populates="word")


class VideoLog(Base):
    __tablename__ = 'video_logs'
    video_id = Column(CHAR(36), primary_key=True)
    script = Column(Text)
    status = Column(Enum(VideoLogStatus), default=VideoLogStatus.PENDING)
    video_url = Column(Text)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)

    words = relationship("Word", backref="video_log_backref")


class PracticeSession(Base):
    __tablename__ = 'practice_sessions'
    session_idx = Column(CHAR(36), primary_key=True)
    user_idx = Column(INTEGER(unsigned=True), ForeignKey('users.user_idx'), nullable=False)
    game_type_idx = Column(CHAR(36), ForeignKey('game_types.game_type_idx'))
    sentence_text = Column(Text)
    created_at = Column(DateTime, default=func.now())
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
    # error_type = Column(Enum(PracticeWordErrorType), default=PracticeWordErrorType.NONE)
    error_type = Column(
        Enum(
            'Omission',
            'Insertion',
            'Mispronunciation',
            'None',
            name='practiceworderrortype'  # 데이터베이스에 생성될 ENUM 타입 이름
        ),
        default='None'  # 기본값도 문자열로 일치
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
        ), nullable=True)  # 이 컬럼은 이제 초성/종성만 저장
    practice_word = relationship("PracticeWord")


class Syllable(Base):
    __tablename__ = 'syllables'
    syllable_char = Column(String(10), primary_key=True)
    gif_url = Column(JSON, nullable=False)
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
    jamo_initial = Column(String(10), nullable=False, index=True)  # ex) 'ㅂ'
    words = Column(JSON, nullable=False)  # ["바다","버섯",...]
    created_at = Column(DateTime, default=func.now(), index=True)


class StageWords(Base):
    __tablename__ = "stage_words"

    stage_id = Column(Integer, primary_key=True, autoincrement=False)
    level = Column(Integer, nullable=False)
    difficulty = Column(Enum(Difficulty), nullable=False)
    goal_value = Column(Integer, nullable=False)
    speed = Column(DECIMAL(3, 1), nullable=False)
    interval_ms = Column(Integer, nullable=False)
    lives = Column(Integer, default=0)
    words = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=func.now())

    progresses = relationship("UserStageProgress", back_populates="stage", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StageWords id={self.stage_id} diff={self.difficulty}>"


class UserStageProgress(Base):
    __tablename__ = "user_stage_progress"

    user_idx = Column(INTEGER(unsigned=True), ForeignKey("users.user_idx"), primary_key=True)
    stage_id = Column(Integer, ForeignKey("stage_words.stage_id"), primary_key=True)
    cleared = Column(TINYINT(1), default=0)
    cleared_at = Column(DateTime, nullable=True)

    stage = relationship("StageWords", back_populates="progresses")
    user = relationship("User", backref="stage_progress")

    def __repr__(self):
        return f"<UserStageProgress user={self.user_idx} stage={self.stage_id} cleared={self.cleared}>"


class EndlessScores(Base):
    __tablename__ = "endless_scores"

    user_idx = Column(INTEGER(unsigned=True), ForeignKey("users.user_idx"), primary_key=True)
    best_score = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    user = relationship("User", backref="endless_score")

    def __repr__(self):
        return f"<EndlessScores user={self.user_idx} score={self.best_score}>"
