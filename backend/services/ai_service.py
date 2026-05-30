import os
import asyncio
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

HF_MODEL = os.getenv("HF_MODEL", "google/flan-t5-base")

_pipeline = None
_pipeline_lock = asyncio.Lock()


async def get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    async with _pipeline_lock:
        if _pipeline is not None:
            return _pipeline
        try:
            from transformers import pipeline
            loop = asyncio.get_event_loop()
            _pipeline = await loop.run_in_executor(
                None,
                lambda: pipeline(
                    "text2text-generation",
                    model=HF_MODEL,
                    max_new_tokens=256,
                    do_sample=False,
                )
            )
            logger.info(f"Loaded HuggingFace model: {HF_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load HF model: {e}")
            _pipeline = None
    return _pipeline


async def generate_ai_response(
    message: str,
    context: Optional[str] = None,
    conversation_history: Optional[list] = None,
) -> str:
    """Generate a response using the HuggingFace model."""
    try:
        pipe = await get_pipeline()

        if context:
            prompt = (
                f"You are StudyMate AI, a helpful study assistant. "
                f"Use the following context from the uploaded document to answer the question.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {message}\n\n"
                f"Answer:"
            )
        else:
            history_text = ""
            if conversation_history:
                recent = conversation_history[-4:]
                history_text = "\n".join(
                    f"{m['role'].capitalize()}: {m['content']}"
                    for m in recent
                )
                history_text = f"Conversation history:\n{history_text}\n\n"

            prompt = (
                f"You are StudyMate AI, a knowledgeable and encouraging study assistant. "
                f"Help students learn effectively. Give clear, concise, accurate answers.\n\n"
                f"{history_text}"
                f"Student: {message}\n\n"
                f"StudyMate AI:"
            )

        if pipe is None:
            return await _fallback_response(message, context)

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: pipe(prompt, max_new_tokens=256, do_sample=False)
        )

        answer = result[0]["generated_text"].strip()
        if not answer:
            return await _fallback_response(message, context)
        return answer

    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return await _fallback_response(message, context)


async def _fallback_response(message: str, context: Optional[str] = None) -> str:
    """Rule-based fallback when model is unavailable."""
    msg_lower = message.lower()

    if context:
        return (
            "📄 Based on the uploaded document, I can see relevant information was found. "
            "However, my AI model is currently loading. "
            "Please try again in a moment for a detailed answer from the document content."
        )

    topic_responses = {
        "math": "Mathematics requires practice and understanding of fundamentals. Break complex problems into smaller steps, show all your work, and practice with varied examples.",
        "physics": "Physics connects math to real-world phenomena. Focus on understanding concepts before formulas. Draw diagrams and work through problems systematically.",
        "chemistry": "Chemistry requires memorizing key concepts but also understanding underlying principles. Use mnemonics for periodic table elements and practice balancing equations daily.",
        "biology": "Biology is a subject of systems. Understand how parts relate to wholes. Use diagrams, flow charts, and connect concepts to real-world examples.",
        "history": "History is about understanding causes and effects. Create timelines, connect events, and understand the human motivations behind historical decisions.",
        "literature": "For literature, focus on themes, character development, and author's intent. Always support your analysis with direct evidence from the text.",
        "programming": "Programming improves with practice. Write code daily, debug methodically, and break large problems into small functions.",
        "essay": "Strong essays have a clear thesis, organized body paragraphs with evidence, and a conclusion that synthesizes your argument.",
    }

    for topic, response in topic_responses.items():
        if topic in msg_lower:
            return f"📚 **{topic.capitalize()} Study Guide**\n\n{response}\n\nWould you like more specific help with {topic}?"

    return (
        "🤖 I'm processing your question. My AI model is warming up — "
        "this can take a moment on first use.\n\n"
        "In the meantime, try asking about:\n"
        "- **study tips** — proven learning strategies\n"
        "- **exam tips** — test preparation advice\n"
        "- **productivity tips** — focus and time management\n\n"
        "Or upload a PDF to ask questions about your study material!"
    )
