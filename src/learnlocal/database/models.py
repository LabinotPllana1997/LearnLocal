"""Database models for educational content tracking."""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Question(Base):
    """Model for tracking questions and responses."""
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    user_type = Column(String(50), default="teacher")
    response_time_ms = Column(Float)
    model_used = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AudioGeneration(Base):
    """Model for tracking audio generation."""
    __tablename__ = "audio_generations"
    
    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, nullable=True)
    text_content = Column(Text, nullable=False)
    voice_type = Column(String(50), default="default")
    speed = Column(Float, default=1.0)
    engine_used = Column(String(50))
    file_path = Column(String(255))
    generation_time_ms = Column(Float)
    created_at = Column(DateTime, default=func.now())

class UsageStats(Base):
    """Model for daily usage statistics."""
    __tablename__ = "usage_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False)
    questions_asked = Column(Integer, default=0)
    audio_generated = Column(Integer, default=0)
    total_response_time_ms = Column(Float, default=0.0)
    avg_response_time_ms = Column(Float, default=0.0)
    most_common_topics = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SystemHealth(Base):
    """Model for system health monitoring."""
    __tablename__ = "system_health"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=func.now())
    cpu_usage = Column(Float)
    memory_usage = Column(Float)
    model_status = Column(String(20))
    tts_engines_available = Column(Text)
    total_questions = Column(Integer, default=0)
    total_audio_files = Column(Integer, default=0)