import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

_model = None
_tokenizer = None
_model_loaded = False
_load_error = None


def load_model():
    """Load SmolLM2-360M-Instruct model once at startup."""
    global _model, _tokenizer, _model_loaded, _load_error
    
    if _model_loaded:
        return True
    
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        model_name = "HuggingFaceTB/SmolLM2-360M-Instruct"
        logger.info(f"Loading model: {model_name}")
        
        _tokenizer = AutoTokenizer.from_pretrained(model_name)
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            low_cpu_mem_usage=True,
        )
        _model.eval()
        _model_loaded = True
        logger.info("Model loaded successfully.")
        return True
    except Exception as e:
        _load_error = str(e)
        logger.error(f"Failed to load model: {e}")
        return False


def _build_prompt(
    user_message: str,
    history: List[Dict[str, str]],
    pdf_context: Optional[str] = None
) -> str:
    """Build a chat prompt using the chat template."""
    messages = []
    
    # System message
    system_content = (
        "You are StudyBot, a helpful and knowledgeable study assistant. "
        "You help students understand concepts, answer academic questions, explain programming topics, "
        "and support learning across all subjects. "
        "Always provide clear, accurate, and educational answers. "
        "Never simply repeat the user's question. "
        "Format your responses with markdown when helpful."
    )
    
    if pdf_context:
        system_content += (
            f"\n\nThe user has uploaded a PDF document. Use the following extracted content to answer their question:\n\n"
            f"--- PDF CONTENT ---\n{pdf_context}\n--- END PDF CONTENT ---\n\n"
            "Base your answer on the PDF content above. If the content doesn't fully answer the question, "
            "supplement with your own knowledge and indicate this."
        )
    
    messages.append({"role": "system", "content": system_content})
    
    # Add conversation history (last 6 exchanges max)
    recent_history = history[-12:] if len(history) > 12 else history
    for msg in recent_history:
        if msg.get("role") in ("user", "assistant"):
            messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    # Apply chat template
    prompt = _tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    return prompt


def _clean_response(raw: str, user_message: str) -> str:
    """Clean and validate the generated response."""
    # Remove any <|...|> tokens that leaked
    cleaned = re.sub(r'<\|[^|]+\|>', '', raw).strip()
    
    # Remove leading whitespace and newlines
    cleaned = cleaned.strip()
    
    # If the response is too short or empty, return a fallback
    if len(cleaned) < 10:
        return "I'm not sure I understood that fully. Could you rephrase your question?"
    
    # Check if the model just repeated the question
    user_lower = user_message.lower().strip()
    response_lower = cleaned.lower().strip()
    
    if response_lower == user_lower or response_lower.startswith(user_lower[:30]):
        return (
            "I'd be happy to help with that topic! However, I need a bit more context. "
            "Could you be more specific about what aspect you'd like me to explain?"
        )
    
    return cleaned


def generate_response(
    user_message: str,
    history: List[Dict[str, str]],
    pdf_context: Optional[str] = None,
    max_new_tokens: int = 400,
    temperature: float = 0.7,
) -> str:
    """Generate an AI response for the user message."""
    global _model, _tokenizer, _model_loaded, _load_error
    
    if not _model_loaded:
        if _load_error:
            return (
                f"⚠️ The AI model could not be loaded: `{_load_error}`\n\n"
                "Please check that all dependencies are installed:\n"
                "```\npip install transformers torch\n```"
            )
        return "⚠️ The AI model is still loading. Please wait a moment and try again."
    
    try:
        import torch
        
        prompt = _build_prompt(user_message, history, pdf_context)
        
        inputs = _tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )
        
        input_ids = inputs["input_ids"]
        input_length = input_ids.shape[1]
        
        with torch.no_grad():
            outputs = _model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.2,
                pad_token_id=_tokenizer.eos_token_id,
                eos_token_id=_tokenizer.eos_token_id,
            )
        
        # Decode only new tokens
        new_tokens = outputs[0][input_length:]
        response_text = _tokenizer.decode(new_tokens, skip_special_tokens=True)
        
        return _clean_response(response_text, user_message)
    
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return (
            f"⚠️ An error occurred while generating a response: `{str(e)}`\n\n"
            "Please try again or rephrase your question."
        )
