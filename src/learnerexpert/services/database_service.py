"""Database service for educational content tracking and analytics."""

import json
import time
from datetime import datetime, date
from typing import List, Optional, Dict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import Question, AudioGeneration, UsageStats, SystemHealth

class DatabaseService:
    """Service for database operations and analytics."""
    
    @staticmethod
    async def save_question_response(
        session: AsyncSession,
        question_text: str,
        answer_text: str,
        user_type: str = "teacher",
        response_time_ms: float = 0.0,
        model_used: str = "unknown"
    ) -> Question:
        """Save a question and its response to the database."""
        question = Question(
            question_text=question_text,
            answer_text=answer_text,
            user_type=user_type,
            response_time_ms=response_time_ms,
            model_used=model_used
        )
        
        session.add(question)
        await session.commit()
        await session.refresh(question)
        return question
    
    @staticmethod
    async def save_audio_generation(
        session: AsyncSession,
        text_content: str,
        voice_type: str = "default",
        speed: float = 1.0,
        engine_used: str = "unknown",
        file_path: str = "",
        generation_time_ms: float = 0.0,
        question_id: Optional[int] = None
    ) -> AudioGeneration:
        """Save audio generation record to the database."""
        audio_gen = AudioGeneration(
            question_id=question_id,
            text_content=text_content,
            voice_type=voice_type,
            speed=speed,
            engine_used=engine_used,
            file_path=file_path,
            generation_time_ms=generation_time_ms
        )
        
        session.add(audio_gen)
        await session.commit()
        await session.refresh(audio_gen)
        return audio_gen
    
    @staticmethod
    async def get_recent_questions(
        session: AsyncSession, 
        limit: int = 50,
        user_type: Optional[str] = None
    ) -> List[Question]:
        """Get recent questions from the database."""
        query = select(Question).order_by(desc(Question.created_at)).limit(limit)
        
        if user_type:
            query = query.where(Question.user_type == user_type)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_question_by_id(session: AsyncSession, question_id: int) -> Optional[Question]:
        """Get a specific question by ID."""
        result = await session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def search_questions(
        session: AsyncSession,
        search_term: str,
        limit: int = 20
    ) -> List[Question]:
        """Search questions by text content."""
        query = select(Question).where(
            Question.question_text.contains(search_term)
        ).order_by(desc(Question.created_at)).limit(limit)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_daily_stats(session: AsyncSession):
        """Update daily usage statistics."""
        today = date.today().isoformat()
        
        questions_count = await session.execute(
            select(func.count(Question.id)).where(
                func.date(Question.created_at) == today
            )
        )
        questions_today = questions_count.scalar() or 0
        
        audio_count = await session.execute(
            select(func.count(AudioGeneration.id)).where(
                func.date(AudioGeneration.created_at) == today
            )
        )
        audio_today = audio_count.scalar() or 0
        
        avg_response_time = await session.execute(
            select(func.avg(Question.response_time_ms)).where(
                func.date(Question.created_at) == today
            )
        )
        avg_time = avg_response_time.scalar() or 0.0
        
        existing_stats = await session.execute(
            select(UsageStats).where(UsageStats.date == today)
        )
        stats = existing_stats.scalar_one_or_none()
        
        if stats:
            stats.questions_asked = questions_today
            stats.audio_generated = audio_today
            stats.avg_response_time_ms = avg_time
            stats.updated_at = datetime.now()
        else:
            stats = UsageStats(
                date=today,
                questions_asked=questions_today,
                audio_generated=audio_today,
                avg_response_time_ms=avg_time
            )
            session.add(stats)
        
        await session.commit()
        return stats
    
    @staticmethod
    async def get_usage_stats(
        session: AsyncSession,
        days: int = 7
    ) -> List[UsageStats]:
        """Get usage statistics for the last N days."""
        query = select(UsageStats).order_by(desc(UsageStats.date)).limit(days)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_analytics_summary(session: AsyncSession) -> Dict:
        """Get a comprehensive analytics summary."""
        
        total_questions = await session.execute(select(func.count(Question.id)))
        total_audio = await session.execute(select(func.count(AudioGeneration.id)))
        
        recent_stats = await DatabaseService.get_usage_stats(session, days=7)
        
        most_active_day = await session.execute(
            select(UsageStats).order_by(desc(UsageStats.questions_asked)).limit(1)
        )
        
        avg_response_time = await session.execute(
            select(func.avg(Question.response_time_ms))
        )
        
        return {
            "total_questions": total_questions.scalar() or 0,
            "total_audio_generated": total_audio.scalar() or 0,
            "recent_activity": [
                {
                    "date": stat.date,
                    "questions": stat.questions_asked,
                    "audio": stat.audio_generated,
                    "avg_response_time": stat.avg_response_time_ms
                }
                for stat in recent_stats
            ],
            "most_active_day": most_active_day.scalar_one_or_none(),
            "overall_avg_response_time": avg_response_time.scalar() or 0.0
        }