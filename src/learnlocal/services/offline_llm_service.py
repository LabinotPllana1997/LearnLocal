"""
Offline LLM service using OpenAI GPT-OSS-20B for educational content generation.
"""

import os
import psutil
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from typing import Optional
import logging
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class OfflineLLMService:
    """Service for offline LLM using OpenAI GPT-OSS-20B."""
    
    def __init__(self, model_name: str = "openai/gpt-oss-20b", device: str = "auto"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
            
        self._load_model()
    
    def _load_model(self):
        """Load the offline LLM model and tokenizer."""
        try:
            logger.info(f"Loading {self.model_name}")
            
            total_ram = psutil.virtual_memory().total / (1024**3)
            available_ram = psutil.virtual_memory().available / (1024**3)
            
            logger.info(f"System RAM: {total_ram:.1f}GB total, {available_ram:.1f}GB available")
            
            model_memory_requirements = {
                "openai/gpt-oss-20b": 6.0,
                "microsoft/DialoGPT-medium": 2.0,
                "microsoft/DialoGPT-small": 0.5,
                "distilgpt2": 0.3
            }
            
            required_ram = model_memory_requirements.get(self.model_name, 8.0)
            logger.info(f"Model requires approximately: {required_ram}GB RAM")
            
            if available_ram < required_ram:
                logger.warning("Insufficient RAM detected!")
                logger.warning(f"Available: {available_ram:.1f}GB, Required: {required_ram}GB")
                logger.warning("This may cause system instability or crashes.")
                logger.warning("RECOMMENDED ALTERNATIVES:")
                logger.warning("1. Use a smaller model: microsoft/DialoGPT-medium (2GB)")
                logger.warning("2. Use distilgpt2 (0.3GB) for very low memory")
                logger.warning("3. Add more RAM to your system")
                logger.warning("4. Use cloud deployment with more RAM")
                
                logger.info("Attempting to free up RAM by cleaning stuck processes...")
                
                import subprocess
                try:
                    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
                    for line in result.stdout.split('\n'):
                        if 'Python main.py' in line or 'python main.py' in line:
                            parts = line.split()
                            if len(parts) > 10 and float(parts[3]) > 5.0:
                                pid = parts[1]
                                subprocess.run(['kill', '-9', pid], capture_output=True)
                                logger.info(f"Cleaned stuck process PID {pid}")
                except:
                    pass
                
                available_ram = psutil.virtual_memory().available / (1024**3)
                logger.info(f"RAM after cleanup: {available_ram:.1f}GB")
                
                if available_ram < required_ram:
                    raise Exception(f"Insufficient RAM even after cleanup: need {required_ram}GB, have {available_ram:.1f}GB")
            
            logger.info("Starting model load...")
            print()
            
            logger.info(f"Loading offline LLM: {self.model_name}")
            
            cache_dir = get_settings().models_cache_dir
            model_cache_path = f"{cache_dir}/models--openai--gpt-oss-20b"
            
            if os.path.exists(model_cache_path):
                print(f"Using cached model from: {model_cache_path}")
            else:
                print("Model not found in local cache, will download from Hugging Face...")
                print(f"Expected location: {model_cache_path}")
                print("Tip: Run 'python setup_model.py' to pre-download the model")
            
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=cache_dir,
                trust_remote_code=True
            )
            logger.info("Tokenizer loaded successfully")
            
            model_kwargs = {
                "cache_dir": cache_dir,
                "trust_remote_code": True,
                "low_cpu_mem_usage": True,
                "torch_dtype": torch.bfloat16,  # Use bfloat16 to match model's natural dtype
                "device_map": "auto" if torch.cuda.is_available() else "cpu",
                "max_memory": {0: "6GB"} if not torch.cuda.is_available() else None,
                "offload_folder": None
            }
            
            if torch.cuda.is_available():
                print(f"Using GPU acceleration")
            else:
                print(f"Using CPU with memory optimizations")
                print(f"Model will use max 6GB RAM with bfloat16 precision and CPU offloading")
            
            logger.info("Loading model (this takes the longest)...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            if not torch.cuda.is_available():
                self.model = self.model.to(self.device)
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("Model loaded successfully")
            logger.info("READY: LearnerExpert Educational Assistant")
            print()
            
            logger.info(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            logger.error("TROUBLESHOOTING:")
            logger.error("1. Run 'python setup_model.py' to download the model first")
            logger.error("2. Ensure you have enough RAM (16GB+ recommended)")
            logger.error("3. Check internet connection if downloading from Hugging Face")
            self.model = None
            self.tokenizer = None
            raise
    
    def _ensure_model_loaded(self):
        """Ensure model is loaded before use."""
        if self.model is None or self.tokenizer is None:
            return False
        return True

    def generate_educational_response(
        self, 
        question: str, 
        context: str = "",
        user_type: str = "teacher",
        max_length: int = 1024
    ) -> str:
        """
        Generate educational response using the offline LLM.
        
        Args:
            question: The educational question
            context: Additional context or curriculum information
            user_type: Type of user (teacher, student)
            max_length: Maximum response length
        """
        if not self._ensure_model_loaded():
            return "I apologize, but the offline language model is currently unavailable. Please check the system configuration or try again later."
        
        try:
            if user_type == "teacher":
                system_message = "You are an expert educational assistant helping teachers create engaging lesson content and answer curriculum questions."
            else:
                system_message = "You are a helpful educational assistant providing clear explanations for learning."
            
            prompt = f"""<|system|>
{system_message}
<|user|>
{context + " " if context else ""}{question}
<|assistant|>
"""
            
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt", 
                truncation=True,
                max_length=1024  # Reduced for stability
            )
            
            if hasattr(self.model, 'device'):
                inputs = inputs.to(self.model.device)
                if hasattr(self.model, 'dtype'):
                    inputs = inputs.to(dtype=torch.long)
            
            import signal
            import threading
            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
            
            def generate_with_timeout():
                logger.debug(f"Starting generation with input shape: {inputs.shape}")
                logger.debug(f"Model device: {getattr(self.model, 'device', 'unknown')}")
                logger.debug(f"Input device: {inputs.device}")
                
                with torch.no_grad():
                    return self.model.generate(
                        inputs,
                        max_new_tokens=min(max_length, 50),
                        num_return_sequences=1,
                        temperature=0.8,
                        do_sample=True,
                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        use_cache=True,
                        early_stopping=True
                    )
            
            try:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(generate_with_timeout)
                    outputs = future.result(timeout=get_settings().llm_generation_timeout)
            except FutureTimeoutError:
                logger.error("Model generation timed out after 30 seconds")
                return "I apologize, but the response generation is taking too long. Please try a simpler question."
            
            full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if "<|assistant|>" in full_response:
                response = full_response.split("<|assistant|>")[-1].strip()
            else:
                response = full_response[len(prompt):].strip()
            
            if not response:
                response = "I'd be happy to help you with that educational topic. Could you provide more specific details about what you'd like to know?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Model device: {getattr(self.model, 'device', 'unknown')}")
            logger.error(f"Inputs shape: {inputs.shape if 'inputs' in locals() else 'not created'}")
            logger.debug(f"Error in text generation: {e}")
            return f"I apologize, but I'm having trouble generating a response right now. Technical error: {str(e)}"
    
    def generate_curriculum_content(
        self,
        topic: str,
        level: str = "intermediate",
        duration: str = "1 hour",
        objectives: list = None
    ) -> dict:
        """Generate curriculum content for a given topic."""
        if not self._ensure_model_loaded():
            return {
                "topic": topic,
                "error": "Offline language model unavailable",
                "modules": [],
                "activities": [],
                "assessments": []
            }
        """Generate structured curriculum content for a topic."""
        
        objectives_text = ""
        if objectives:
            objectives_text = f"Learning objectives: {', '.join(objectives)}. "
        
        question = f"""Create a comprehensive {duration} lesson plan for teaching "{topic}" at {level} level. {objectives_text}
        
Please provide:
1. Learning objectives
2. Key concepts to cover
3. Activities and exercises
4. Assessment methods
5. Resources needed"""
        
        response = self.generate_educational_response(
            question=question,
            user_type="teacher",
            max_length=1500
        )
        
        return {
            "topic": topic,
            "level": level,
            "duration": duration,
            "content": response,
            "generated_by": self.model_name
        }
    
    def is_loaded(self) -> bool:
        """Check if model is properly loaded."""
        return self.model is not None and self.tokenizer is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "model_loaded": self.model is not None,
            "tokenizer_loaded": self.tokenizer is not None,
            "cuda_available": torch.cuda.is_available(),
            "memory_usage_gb": torch.cuda.memory_allocated() / 1e9 if torch.cuda.is_available() else 0
        }