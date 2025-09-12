"""
Offline educational endpoints with LLM, TTS, and database integration.
"""

import time
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.unified_llm_service import get_unified_llm_service
from ...services.tts_service import TTSService
from ...services.database_service import DatabaseService
from ...database import get_database_session
from ...config.settings import get_settings
from ...prompts import (
    TEACHER_SYSTEM_PROMPT, 
    STUDENT_SYSTEM_PROMPT, 
    CURRICULUM_PROMPT, 
    LESSON_PROMPT, 
    QA_PROMPT
)

router = APIRouter(prefix="/api", tags=["offline"])

settings = get_settings()
llm_service = get_unified_llm_service()
tts_service = TTSService() if settings.tts_enabled else None

def format_lesson_for_ui(raw_content: str, topic: str) -> str:
    """Format lesson content for React Native mobile UI display."""
    try:
        lesson_data = json.loads(raw_content)
        
        if isinstance(lesson_data, dict):
            formatted_sections = []
            
            title = lesson_data.get('title', f'Lesson: {topic}')
            formatted_sections.append(f"{title}")
            formatted_sections.append("") 
            
            if 'content' in lesson_data:
                content = lesson_data['content'].strip()
                content = content.replace('##', '').replace('#', '').strip()
                paragraphs = content.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        formatted_sections.append(para.strip())
                        formatted_sections.append("")
            
            if 'keyPoints' in lesson_data and lesson_data['keyPoints']:
                formatted_sections.append("🔑 KEY POINTS:")
                formatted_sections.append("")
                for point in lesson_data['keyPoints']:
                    formatted_sections.append(f"• {point}")
                formatted_sections.append("")
            
            if 'activities' in lesson_data and lesson_data['activities']:
                formatted_sections.append("🎯 ACTIVITIES:")
                formatted_sections.append("")
                for i, activity in enumerate(lesson_data['activities'], 1):
                    formatted_sections.append(f"{i}. {activity}")
                formatted_sections.append("")
            
            if 'estimatedDuration' in lesson_data:
                formatted_sections.append(f"⏱️ Duration: {lesson_data['estimatedDuration']} minutes")
            
            return '\n'.join(formatted_sections)
    
    except json.JSONDecodeError:
        pass
    
    lines = raw_content.strip().split('\n')
    formatted_sections = []
    
    formatted_sections.append(f"Lesson: {topic}")
    formatted_sections.append("")
    
    current_section = ""
    for line in lines:
        line = line.strip()
        if not line:
            if current_section:
                formatted_sections.append("")
            continue
        
        line = line.replace('##', '').replace('#', '').replace('**', '').strip()
        
        if any(keyword in line.lower() for keyword in ['objective', 'goal', 'introduction', 'overview']):
            formatted_sections.append(f"🎯 {line.upper()}")
            formatted_sections.append("")
        elif any(keyword in line.lower() for keyword in ['key point', 'important', 'remember']):
            formatted_sections.append(f"🔑 {line.upper()}")
            formatted_sections.append("")
        elif any(keyword in line.lower() for keyword in ['activity', 'exercise', 'practice']):
            formatted_sections.append(f"🎯 {line.upper()}")
            formatted_sections.append("")
        elif any(keyword in line.lower() for keyword in ['summary', 'conclusion', 'recap']):
            formatted_sections.append(f"📝 {line.upper()}")
            formatted_sections.append("")
        elif line.startswith('-') or line.startswith('•'):
            formatted_sections.append(f"• {line[1:].strip()}")
        elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
            formatted_sections.append(line)
        else:
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) > 80:
                        formatted_sections.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line.strip():
                    formatted_sections.append(current_line.strip())
            else:
                formatted_sections.append(line)
            formatted_sections.append("")
    
    return '\n'.join(formatted_sections)

def format_chat_response_for_ui(raw_content: str) -> str:
    """Format chat response for React Native mobile UI display."""
    lines = raw_content.strip().split('\n')
    formatted_sections = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        line = line.replace('**', '').replace('##', '').replace('#', '').strip()
        
        if line.startswith('-') or line.startswith('•'):
            formatted_sections.append(f"• {line[1:].strip()}")
        elif line.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            formatted_sections.append(line)
        else:
            if len(line) > 80:
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line + word) > 80:
                        formatted_sections.append(current_line.strip())
                        current_line = word + " "
                    else:
                        current_line += word + " "
                if current_line.strip():
                    formatted_sections.append(current_line.strip())
            else:
                formatted_sections.append(line)
        
        formatted_sections.append("")
    
    while formatted_sections and formatted_sections[-1] == "":
        formatted_sections.pop()
    
    return '\n'.join(formatted_sections)

class QuestionRequest(BaseModel):
    """Request model for educational questions."""
    question: str
    context: str = ""
    user_type: str = "teacher"
    include_audio: bool = False
    model: str = "gpt-oss:20b"  

class ChatRequest(BaseModel):
    """Request model for educational questions."""
    message: str
    model: str = "gpt-oss:20b"

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
    model: str = "gpt-oss:20b"  

class Message(BaseModel):
    """Individual message in lesson generation request."""
    role: str
    content: str

class LessonGenerationRequest(BaseModel):
    """Request model for lesson generation - matches HarmonyRequest interface."""
    conversation: Optional[dict] = None
    messages: Optional[list[Message]] = None
    model: str = "gpt-oss:20b"
    maxTokens: int = 2000

@router.get("/health")
async def api_health_check():
    """Health check endpoint for API compatibility."""
    try:
        model_status = "available" if llm_service.is_model_loaded() else "loading"
        return {
            "status": "healthy" if llm_service.is_model_loaded() else "loading",
            "model": settings.offline_llm_model
        }
    except Exception as e:
        return {
            "status": "error",
            "model": "unavailable"
        }

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
        
        from ...llm.ollama_client import get_ollama_manager
        ollama = get_ollama_manager()
        
        system_message = TEACHER_SYSTEM_PROMPT if request.user_type == "teacher" else STUDENT_SYSTEM_PROMPT
        context_text = f"\n\nContext: {request.context}" if request.context else ""
        
        prompt = QA_PROMPT.format(
            system_message=system_message,
            question=request.question,
            context_text=context_text
        )
        
        raw_response = ollama.generate_response(
            prompt=prompt,
            model=request.model,
            max_tokens=512,
            temperature=0.7
        )
        
        formatted_response = format_chat_response_for_ui(raw_response)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        question_record = await DatabaseService.save_question_response(
            session=db,
            question_text=request.question,
            answer_text=formatted_response,
            user_type=request.user_type,
            response_time_ms=response_time_ms,
            model_used=request.model
        )
        
        await DatabaseService.update_daily_stats(db)
        
        return {
            "response": formatted_response,
            "model": request.model,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.post("/chat")
async def chat(
    request: ChatRequest
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
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        from ...llm.ollama_client import get_ollama_manager
        ollama = get_ollama_manager()
        
        response = ollama.generate_response(
            prompt=request.message,
            model=request.model,
            max_tokens=2000,
            temperature=0.7
        )
        
        return {
            "response": response,
            "model": request.model,
            "timestamp": datetime.now().isoformat()
        }
        
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
        
        from ...llm.ollama_client import get_ollama_manager
        ollama = get_ollama_manager()
        
        objectives_text = ""
        if request.objectives:
            objectives_text = f"Learning objectives: {', '.join(request.objectives)}. "
        
        prompt = CURRICULUM_PROMPT.format(
            topic=request.topic,
            level=request.level,
            duration=request.duration,
            objectives_text=objectives_text
        )
        
        content = ollama.generate_response(
            prompt=prompt,
            model=request.model,
            max_tokens=1500,
            temperature=0.7
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        await DatabaseService.save_question_response(
            session=db,
            question_text=f"Generate curriculum for: {request.topic}",
            answer_text=content,
            user_type="teacher",
            response_time_ms=response_time_ms,
            model_used=request.model
        )
        await DatabaseService.update_daily_stats(db)
        return {
            "topic": request.topic,
            "level": request.level,
            "duration": request.duration,
            "content": content,
            "model": request.model,
            "response_time_ms": response_time_ms
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating curriculum: {str(e)}")

@router.options("/generate-lesson")
async def generate_lesson_options():
    """Handle CORS preflight for lesson generation."""
    return {}

@router.post("/generate-lesson")
async def generate_lesson(
    request: LessonGenerationRequest,
    db: AsyncSession = Depends(get_database_session)
):
    """Generate educational lesson content using offline LLM."""
    try:
        if not settings.offline_llm_enabled:
            raise HTTPException(status_code=503, detail="Offline LLM model not enabled")
        if not llm_service.is_model_loaded():
            return {
                "status": "loading",
                "message": "Offline LLM model is still loading. Please try again in a moment."
            }
        
        messages = []
        if request.messages:
            messages = request.messages
        elif request.conversation:
            if isinstance(request.conversation, dict):
                if 'messages' in request.conversation:
                    conv_messages = request.conversation['messages']
                    messages = [Message(role=msg.get("role", "user"), content=msg.get("content", "")) 
                               for msg in conv_messages if isinstance(msg, dict)]
                else:
                    messages = [Message(role=msg.get("role", "user"), content=msg.get("content", "")) 
                               for msg in [request.conversation] if isinstance(request.conversation, dict)]
            elif isinstance(request.conversation, list):
                messages = [Message(role=msg.get("role", "user"), content=msg.get("content", "")) 
                           for msg in request.conversation if isinstance(msg, dict)]
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided in request")
        
        system_content = ""
        developer_content = ""
        user_content = ""
        
        for message in messages:
            if message.role == "system":
                system_content = message.content
            elif message.role == "developer":
                developer_content = message.content
            elif message.role == "user":
                user_content = message.content
        
        prompt = LESSON_PROMPT.format(
            system_content=system_content,
            developer_content=developer_content,
            user_content=user_content
        )
        
        start_time = time.time()
        
        from ...llm.ollama_client import get_ollama_manager
        ollama = get_ollama_manager()
        
        raw_response = ollama.generate_response(
            prompt=prompt,
            model=request.model,
            max_tokens=request.maxTokens,
            temperature=0.7
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        token_estimate = len(raw_response.split()) * 1.3
        
        formatted_content = format_lesson_for_ui(raw_response, user_content)
        
        await DatabaseService.save_question_response(
            session=db,
            question_text=f"Generate lesson: {user_content}",
            answer_text=formatted_content,
            user_type="teacher",
            response_time_ms=response_time_ms,
            model_used=request.model
        )
        
        await DatabaseService.update_daily_stats(db)
        
        return {
            "content": formatted_content,
            "tokens": int(token_estimate),
            "model": request.model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating lesson: {str(e)}")

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