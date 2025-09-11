"""
Offline educational endpoints with LLM, TTS, and database integration.
"""

import time
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.unified_llm_service import get_unified_llm_service
from ...services.tts_service import TTSService
from ...services.database_service import DatabaseService
from ...database import get_database_session
from ...config.settings import get_settings

router = APIRouter(prefix="/offline", tags=["offline"])

settings = get_settings()
llm_service = get_unified_llm_service()
tts_service = TTSService() if settings.tts_enabled else None

class QuestionRequest(BaseModel):
    """Request model for educational questions."""
    question: str
    context: str = ""
    user_type: str = "teacher"
    include_audio: bool = False

class TTSRequest(BaseModel):
    """Request model for text-to-speech."""
    text: str
    voice_type: str = "default"
    speed: float = 1.0

class CurriculumRequest(BaseModel):
    """Request model for curriculum generation."""
    topic: str
    level: str = "intermediate"
    duration: str = "1 hour"
    objectives: Optional[list] = None

@router.get("/status")
async def get_offline_status():
    """Get status of offline services."""
    return {
        "offline_llm_enabled": settings.offline_llm_enabled,
        "offline_llm_loaded": llm_service.is_model_loaded() if settings.offline_llm_enabled else False,
        "tts_enabled": settings.tts_enabled,
        "tts_engines": tts_service.get_available_engines() if tts_service else [],
        "backend_info": llm_service.get_backend_info() if settings.offline_llm_enabled else {},
        "model_loading": not llm_service.is_model_loaded() if settings.offline_llm_enabled else False
    }

@router.post("/ask")
async def ask_question(
    request: QuestionRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Ask an educational question using offline LLM."""
    try:
        if not settings.offline_llm_enabled:
            raise HTTPException(status_code=503, detail="Offline LLM model not enabled")
        if not llm_service.is_model_loaded():
            return {
                "status": "loading",
                "message": "Offline LLM model is still loading. Please try again in a moment."
            }
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        start_time = time.time()
        
        response = llm_service.generate_educational_response(
            question=request.question,
            context=request.context,
            user_type=request.user_type
        )
        response_time_ms = (time.time() - start_time) * 1000
        
        question_record = await DatabaseService.save_question_response(
            session=db,
            question_text=request.question,
            answer_text=response,
            user_type=request.user_type,
            response_time_ms=response_time_ms,
            model_used=settings.offline_llm_model
        )
        
        await DatabaseService.update_daily_stats(db)
        
        result = {
            "id": question_record.id,
            "question": request.question,
            "answer": response,
            "user_type": request.user_type,
            "response_time_ms": response_time_ms,
            "created_at": question_record.created_at
        }
        
        if request.include_audio and tts_service:
            try:
                audio_start = time.time()
                audio_file = await tts_service.generate_speech(
                    text=response,
                    voice_type="default",
                    speed=settings.tts_speed
                )
                audio_time_ms = (time.time() - audio_start) * 1000
                await DatabaseService.save_audio_generation(
                    session=db,
                    text_content=response,
                    voice_type="default",
                    speed=settings.tts_speed,
                    engine_used="pyttsx3",
                    file_path=audio_file,
                    generation_time_ms=audio_time_ms,
                    question_id=question_record.id
                )
                result["audio_file"] = f"/offline/audio/{uuid.uuid4().hex[:8]}.wav"
                result["audio_generation_time_ms"] = audio_time_ms
            except Exception as e:
                result["audio_error"] = str(e)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/tts")
async def text_to_speech(
    request: TTSRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Convert text to speech."""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS service not available")
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        start_time = time.time()
        audio_file = await tts_service.generate_speech(
            text=request.text,
            voice_type=request.voice_type,
            speed=request.speed
        )
        generation_time_ms = (time.time() - start_time) * 1000
        
        await DatabaseService.save_audio_generation(
            session=db,
            text_content=request.text,
            voice_type=request.voice_type,
            speed=request.speed,
            engine_used="pyttsx3",
            file_path=audio_file,
            generation_time_ms=generation_time_ms
        )
        
        return FileResponse(
            audio_file,
            media_type="audio/wav",
            filename=f"speech_{uuid.uuid4().hex[:8]}.wav"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating speech: {str(e)}")

@router.post("/curriculum")
async def generate_curriculum(
    request: CurriculumRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Generate curriculum content using offline LLM."""
    try:
        if not settings.offline_llm_enabled:
            raise HTTPException(status_code=503, detail="Offline LLM model not enabled")
        if not llm_service.is_model_loaded():
            return {
                "status": "loading",
                "message": "Offline LLM model is still loading. Please try again in a moment."
            }
        start_time = time.time()
        
        curriculum = llm_service.generate_curriculum_content(
            topic=request.topic,
            level=request.level,
            duration=request.duration,
            objectives=request.objectives
        )
        response_time_ms = (time.time() - start_time) * 1000
        await DatabaseService.save_question_response(
            session=db,
            question_text=f"Generate curriculum for: {request.topic}",
            answer_text=curriculum["content"],
            user_type="teacher",
            response_time_ms=response_time_ms,
            model_used=settings.offline_llm_model
        )
        await DatabaseService.update_daily_stats(db)
        return {
            **curriculum,
            "response_time_ms": response_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating curriculum: {str(e)}")

@router.get("/history/questions")
async def get_question_history(
    limit: int = 50,
    user_type: Optional[str] = None,
    db: AsyncSession = Depends(get_database_session)
):
    """Get recent questions and answers."""
    try:
        questions = await DatabaseService.get_recent_questions(db, limit, user_type)
        return {
            "questions": [
                {
                    "id": q.id,
                    "question": q.question_text,
                    "answer": q.answer_text,
                    "user_type": q.user_type,
                    "response_time_ms": q.response_time_ms,
                    "model_used": q.model_used,
                    "created_at": q.created_at
                }
                for q in questions
            ],
            "total": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary(db: AsyncSession = Depends(get_database_session)):
    """Get comprehensive analytics summary."""
    try:
        summary = await DatabaseService.get_analytics_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")