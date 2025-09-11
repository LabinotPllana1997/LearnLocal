"""
Offline educational endpoints with LLM, TTS, and database integration.
"""

import time
import uuid
import json
from datetime import datetime
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

router = APIRouter(prefix="/api", tags=["offline"])

settings = get_settings()
llm_service = get_unified_llm_service()
tts_service = TTSService() if settings.tts_enabled else None

def format_lesson_for_ui(raw_content: str, topic: str) -> str:
    """Format lesson content for mobile UI display."""
    try:
        # Try to parse as JSON first
        lesson_data = json.loads(raw_content)
        
        # If it's already structured JSON, format it nicely
        if isinstance(lesson_data, dict):
            formatted = f"# {lesson_data.get('title', f'Lesson: {topic}')}\n\n"
            
            if 'content' in lesson_data:
                formatted += f"{lesson_data['content']}\n\n"
            
            if 'keyPoints' in lesson_data and lesson_data['keyPoints']:
                formatted += "## 🔑 Key Points:\n"
                for point in lesson_data['keyPoints']:
                    formatted += f"• {point}\n"
                formatted += "\n"
            
            if 'activities' in lesson_data and lesson_data['activities']:
                formatted += "## 🎯 Activities:\n"
                for i, activity in enumerate(lesson_data['activities'], 1):
                    formatted += f"{i}. {activity}\n"
                formatted += "\n"
            
            if 'estimatedDuration' in lesson_data:
                formatted += f"⏱️ **Estimated Duration:** {lesson_data['estimatedDuration']} minutes\n"
            
            return formatted
    
    except json.JSONDecodeError:
        pass
    
    # If not JSON, format as plain text with structure
    lines = raw_content.strip().split('\n')
    formatted = f"# Lesson: {topic}\n\n"
    
    current_section = ""
    for line in lines:
        line = line.strip()
        if not line:
            formatted += "\n"
            continue
            
        # Detect and format headers
        if any(keyword in line.lower() for keyword in ['objective', 'goal', 'introduction', 'overview']):
            formatted += f"## 🎯 {line}\n\n"
        elif any(keyword in line.lower() for keyword in ['key point', 'important', 'remember']):
            formatted += f"## 🔑 {line}\n\n"
        elif any(keyword in line.lower() for keyword in ['activity', 'exercise', 'practice']):
            formatted += f"## 🎯 {line}\n\n"
        elif any(keyword in line.lower() for keyword in ['summary', 'conclusion', 'recap']):
            formatted += f"## 📝 {line}\n\n"
        elif line.startswith('-') or line.startswith('•'):
            formatted += f"{line}\n"
        elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
            formatted += f"{line}\n"
        else:
            formatted += f"{line}\n\n"
    
    return formatted

def format_chat_response_for_ui(raw_content: str) -> str:
    """Format chat response for mobile UI display."""
    # Clean up the response for better mobile display
    lines = raw_content.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Add proper spacing and formatting
        if line.startswith('-') or line.startswith('•'):
            formatted_lines.append(f"• {line[1:].strip()}")
        elif line.startswith(('1.', '2.', '3.', '4.', '5.')):
            formatted_lines.append(f"\n{line}")
        elif len(line) > 100:  # Long lines, add some structure
            formatted_lines.append(f"{line}\n")
        else:
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

# class QuestionRequest(BaseModel):
#     """Request model for educational questions."""
#     question: str
#     context: str = ""
#     user_type: str = "teacher"
#     include_audio: bool = False

class QuestionRequest(BaseModel):
    """Request model for educational questions."""
    message: str
    model: str = "gpt-oss-20b"

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

class Message(BaseModel):
    """Individual message in lesson generation request."""
    role: str
    content: str

class LessonGenerationRequest(BaseModel):
    """Request model for lesson generation - matches HarmonyRequest interface."""
    conversation: Optional[dict] = None
    messages: Optional[list[Message]] = None
    model: str = "gpt-oss"
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

@router.post("/chat")
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
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        start_time = time.time()
        
        # Generate response using the message field
        raw_response = llm_service.generate_response(
            prompt=request.message,
            max_tokens=100,  # Use the current max_tokens setting
            temperature=0.7
        )
        
        # Format response for UI display
        formatted_response = format_chat_response_for_ui(raw_response)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Save to database
        question_record = await DatabaseService.save_question_response(
            session=db,
            question_text=request.message,
            answer_text=formatted_response,
            user_type="user",
            response_time_ms=response_time_ms,
            model_used=request.model
        )
        
        await DatabaseService.update_daily_stats(db)
        
        # Return in ChatResponse format expected by frontend
        return {
            "response": formatted_response,
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
        
        # Handle both conversation (legacy) and messages formats
        messages = []
        if request.messages:
            messages = request.messages
        elif request.conversation and isinstance(request.conversation, list):
            # Convert conversation array to messages
            messages = [Message(role=msg.get("role", "user"), content=msg.get("content", "")) 
                       for msg in request.conversation if isinstance(msg, dict)]
        elif request.conversation and hasattr(request.conversation, 'messages'):
            # Handle nested conversation structure
            conv_messages = getattr(request.conversation, 'messages', [])
            messages = [Message(role=msg.get("role", "user"), content=msg.get("content", "")) 
                       for msg in conv_messages if isinstance(msg, dict)]
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages provided in request")
        
        # Extract information from messages
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
        
        # Build comprehensive prompt for lesson generation
        prompt = f"""{system_content}

{developer_content}

User Request: {user_content}

Please generate a comprehensive educational lesson in a clean, structured format suitable for mobile app display. Use clear sections with headers and bullet points where appropriate. Make the content engaging and easy to read on a mobile device."""
        
        start_time = time.time()
        
        # Generate lesson using the unified LLM service
        raw_response = llm_service.generate_response(
            prompt=prompt,
            max_tokens=request.maxTokens,
            temperature=0.7
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # Calculate token estimate (rough approximation)
        token_estimate = len(raw_response.split()) * 1.3  # Rough token estimation
        
        # Format the response for UI display
        formatted_content = format_lesson_for_ui(raw_response, user_content)
        
        # Save to database
        await DatabaseService.save_question_response(
            session=db,
            question_text=f"Generate lesson: {user_content}",
            answer_text=formatted_content,
            user_type="teacher",
            response_time_ms=response_time_ms,
            model_used=settings.offline_llm_model
        )
        
        await DatabaseService.update_daily_stats(db)
        
        # Return in HarmonyResponse format expected by frontend
        return {
            "content": formatted_content,
            "tokens": int(token_estimate),
            "model": settings.offline_llm_model
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating lesson: {str(e)}")

@router.get("/modules")
async def get_learning_modules():
    """Get available learning modules for the frontend."""
    # Return sample modules for now - this can be expanded later
    sample_modules = [
        {
            "id": "ai-basics",
            "title": "AI Fundamentals",
            "description": "Learn the basics of Artificial Intelligence",
            "content": "Introduction to AI concepts, machine learning, and practical applications",
            "difficulty": "beginner"
        },
        {
            "id": "programming-101",
            "title": "Programming Basics",
            "description": "Introduction to programming concepts",
            "content": "Variables, functions, loops, and basic programming structures",
            "difficulty": "beginner"
        },
        {
            "id": "data-science",
            "title": "Data Science Fundamentals",
            "description": "Understanding data analysis and visualization",
            "content": "Data collection, cleaning, analysis, and visualization techniques",
            "difficulty": "intermediate"
        }
    ]
    
    return sample_modules

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