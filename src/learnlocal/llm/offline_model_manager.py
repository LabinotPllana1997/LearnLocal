import logging
import threading
import torch
from typing import Optional, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

from learnlocal.config.settings import get_settings

logger = logging.getLogger(__name__)


class OfflineModelManager:
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.settings = get_settings()
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._model_name = None
        self._device = None
        self._is_loaded = False
        self._load_lock = threading.Lock()
        
        self._initialized = True
        logger.info("OfflineModelManager initialized")
    
    def _determine_device(self) -> str:
        device_setting = self.settings.offline_llm_device.lower()
        
        if "gpt-oss-20b" in self.settings.offline_llm_model.lower():
            logger.info("Forcing CPU device for large GPT-20B model to avoid memory issues")
            return "cpu"
        
        if device_setting == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                try:
                    test_tensor = torch.ones(1000, 1000, device="mps")
                    del test_tensor
                    return "mps"
                except Exception:
                    logger.warning("MPS available but insufficient memory, falling back to CPU")
                    return "cpu"
            else:
                return "cpu"
        else:
            return device_setting
    
    def load_model(self, force_reload: bool = False) -> bool:
        """
        Load the model into memory if not already loaded.
        
        Args:
            force_reload: Force reload even if model is already loaded
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        if not self.settings.offline_llm_enabled:
            logger.info("Offline LLM is disabled")
            return False
        
        with self._load_lock:
            if (self._is_loaded and 
                self._model_name == self.settings.offline_llm_model and 
                not force_reload):
                logger.debug("Model already loaded, skipping reload")
                return True
            
            try:
                model_name = self.settings.offline_llm_model
                device = self._determine_device()
                
                logger.info(f"Loading offline model: {model_name} on {device}")
                
                logger.info("Loading tokenizer...")
                self._tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    trust_remote_code=True,
                    padding_side="left"
                )
                
                if self._tokenizer.pad_token is None:
                    self._tokenizer.pad_token = self._tokenizer.eos_token
                
                self._tokenizer.padding_side = "left"
                
                logger.info("Loading model with performance optimizations...")
                model_kwargs = {
                    "trust_remote_code": True,
                    "low_cpu_mem_usage": True,
                    "use_cache": True,
                }
                
                use_quantization = getattr(self.settings, 'use_quantization', False)
                quantization_bits = getattr(self.settings, 'quantization_bits', 8)
                
                if use_quantization and quantization_bits == 4:
                    try:
                        from transformers import BitsAndBytesConfig
                        quantization_config = BitsAndBytesConfig(
                            load_in_4bit=True,
                            bnb_4bit_compute_dtype=torch.bfloat16,
                            bnb_4bit_use_double_quant=True,
                            bnb_4bit_quant_type="nf4"
                        )
                        model_kwargs["quantization_config"] = quantization_config
                        model_kwargs["device_map"] = "auto"
                        logger.info("Using 4-bit quantization for faster inference")
                    except ImportError:
                        logger.warning("BitsAndBytes not available, falling back to standard loading")
                        use_quantization = False
                        
                elif use_quantization and quantization_bits == 8:
                    try:
                        model_kwargs["load_in_8bit"] = True
                        model_kwargs["device_map"] = "auto" 
                        logger.info("Using 8-bit quantization for faster inference")
                    except Exception:
                        logger.warning("8-bit quantization failed, falling back to standard loading")
                        use_quantization = False
                
                if not use_quantization:
                    if device == "cpu":
                        model_kwargs.update({
                            "torch_dtype": torch.bfloat16,
                            "device_map": "cpu",
                            "max_memory": {"cpu": "2GB"},
                            "offload_folder": None,
                            "use_safetensors": True
                        })
                    elif device == "cuda":
                        model_kwargs.update({
                            "torch_dtype": torch.bfloat16,
                            "device_map": "auto"
                        })
                        try:
                            model_kwargs["attn_implementation"] = "flash_attention_2"
                        except:
                            pass
                    elif device == "mps":
                        model_kwargs.update({
                            "torch_dtype": torch.float32,
                            "device_map": "cpu",
                            "max_memory": {"cpu": "6GB"}
                        })
                
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    **model_kwargs
                )
                
                logger.info("Creating inference pipeline...")
                
                pipeline_kwargs = {
                    "model": self._model,
                    "tokenizer": self._tokenizer,
                    "torch_dtype": model_kwargs["torch_dtype"],
                    "return_full_text": False,
                    "do_sample": True,
                    "temperature": self.settings.temperature,
                    "max_new_tokens": self.settings.max_tokens,
                    "pad_token_id": self._tokenizer.eos_token_id
                }
                
                if "device_map" not in model_kwargs:
                    pipeline_kwargs["device"] = 0 if device == "cuda" else -1
                
                self._pipeline = pipeline(
                    "text-generation",
                    **pipeline_kwargs
                )
                
                self._model_name = model_name
                self._device = device
                self._is_loaded = True
                
                logger.info(f"Model loaded successfully on {device}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._cleanup()
                return False
    
    def generate_response(
        self, 
        prompt: str, 
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate response using the loaded model with optimizations.
        
        Args:
            prompt: Input prompt
            max_tokens: Override max tokens
            temperature: Override temperature
            **kwargs: Additional generation parameters
            
        Returns:
            Generated response text
        """
        if not self._is_loaded:
            if not self.load_model():
                return "Error: Could not load offline model"
        
        try:
            generation_kwargs = {
                "max_new_tokens": 50,
                "do_sample": False,
                "num_beams": 1,
                "use_cache": True,
                "pad_token_id": self._tokenizer.eos_token_id,
                **kwargs
            }
            
            logger.debug(f"Generating response for prompt: {prompt[:50]}...")
            
            inputs = self._tokenizer(prompt, return_tensors="pt", padding=False)
            
            try:
                if hasattr(self._model, 'device'):
                    model_device = self._model.device
                elif hasattr(self._model, 'parameters'):
                    model_device = next(self._model.parameters()).device
                else:
                    model_device = "cpu"
                
                inputs = {k: v.to(model_device) for k, v in inputs.items()}
            except Exception as e:
                logger.debug(f"Could not move inputs to model device: {e}")
            
            import torch
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    **generation_kwargs
                )
            
            response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            generated_text = response[len(prompt):].strip()
            
            logger.debug(f"Generated response: {len(generated_text)} characters")
            return generated_text if generated_text else "Response generated but appears empty."
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error generating response: {str(e)}"
    
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded."""
        return self._is_loaded
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the currently loaded model."""
        return {
            "model_name": self._model_name,
            "device": self._device,
            "is_loaded": self._is_loaded,
            "enabled": self.settings.offline_llm_enabled
        }
    
    def unload_model(self) -> None:
        """Unload the model from memory."""
        with self._load_lock:
            logger.info("Unloading model...")
            self._cleanup()
            logger.info("Model unloaded")
    
    def _cleanup(self) -> None:
        """Clean up model resources."""
        try:
            if self._pipeline is not None:
                del self._pipeline
                self._pipeline = None
            
            if self._model is not None:
                del self._model
                self._model = None
            
            if self._tokenizer is not None:
                del self._tokenizer
                self._tokenizer = None
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self._is_loaded = False
            self._model_name = None
            self._device = None
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


_model_manager = None
_manager_lock = threading.Lock()


def get_model_manager() -> OfflineModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        with _manager_lock:
            if _model_manager is None:
                _model_manager = OfflineModelManager()
    return _model_manager


def preload_model() -> bool:
    """Preload the model on application startup."""
    logger.info("Preloading offline model...")
    manager = get_model_manager()
    return manager.load_model()


def generate_offline_response(
    prompt: str, 
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> str:
    """
    Generate response using offline model.
    
    Convenience function that handles model loading automatically.
    """
    manager = get_model_manager()
    return manager.generate_response(
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        **kwargs
    )