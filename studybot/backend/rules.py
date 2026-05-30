import re
from typing import Optional

RULES = {
    "greetings": {
        "patterns": [
            r"^(hi|hello|hey|good\s+morning|good\s+evening|good\s+afternoon|howdy|greetings)\b",
        ],
        "response": (
            "## 👋 Hello! Welcome to StudyBot!\n\n"
            "I'm your AI-powered study assistant. I can help you:\n\n"
            "- 📚 **Answer questions** on any subject\n"
            "- 💡 **Explain concepts** clearly\n"
            "- 📄 **Analyze PDFs** — upload a document and ask questions about it\n"
            "- 🧠 **Provide study & exam tips**\n\n"
            "What would you like to study today?"
        ),
    },
    "help": {
        "patterns": [
            r"\b(help|commands|what can you do|capabilities|features)\b",
        ],
        "response": (
            "## 🛠️ StudyBot Commands\n\n"
            "**Chat & Learning**\n"
            "- Ask me anything: *\"What is machine learning?\"*\n"
            "- Explain topics: *\"Explain recursion in Python\"*\n"
            "- Comparisons: *\"Difference between stack and queue\"*\n\n"
            "**PDF Features**\n"
            "- Upload a PDF from the sidebar\n"
            "- Activate it, then ask: *\"Summarize chapter 2\"*\n"
            "- Ask: *\"What are the key findings?\"*\n\n"
            "**Study Help**\n"
            "- Type **study tips** for study strategies\n"
            "- Type **exam tips** for exam preparation\n"
            "- Type **productivity tips** for focus techniques\n\n"
            "What do you need help with?"
        ),
    },
    "study_tips": {
        "patterns": [
            r"\b(study tips?|how to study|study strategies?|study techniques?|study methods?)\b",
        ],
        "response": (
            "## 📚 Effective Study Tips\n\n"
            "**1. Active Recall**\n"
            "Test yourself instead of re-reading. Use flashcards or write answers from memory.\n\n"
            "**2. Spaced Repetition**\n"
            "Review material at increasing intervals: 1 day → 3 days → 1 week → 1 month.\n\n"
            "**3. The Pomodoro Technique**\n"
            "Study for 25 minutes, then take a 5-minute break. After 4 sessions, take a 20-minute break.\n\n"
            "**4. Feynman Technique**\n"
            "Explain the concept in simple terms as if teaching a child. If you can't, you don't understand it yet.\n\n"
            "**5. Mind Mapping**\n"
            "Create visual diagrams to connect related concepts and see the big picture.\n\n"
            "**6. Eliminate Distractions**\n"
            "Put your phone away, use website blockers, and find a quiet study environment.\n\n"
            "**7. Get Enough Sleep**\n"
            "Memory consolidation happens during sleep. Never sacrifice sleep for last-minute cramming."
        ),
    },
    "exam_tips": {
        "patterns": [
            r"\b(exam tips?|exam prep(aration)?|test tips?|how to prepare for (an )?exam|before (an )?exam)\b",
        ],
        "response": (
            "## 🎯 Exam Preparation Tips\n\n"
            "**Before the Exam**\n"
            "- Start reviewing at least one week in advance\n"
            "- Create a study schedule and stick to it\n"
            "- Focus on past papers and sample questions\n"
            "- Identify weak areas and spend extra time there\n\n"
            "**The Night Before**\n"
            "- Do a light review — don't cram new material\n"
            "- Prepare everything you need (pen, ID, water)\n"
            "- Sleep at least 7–8 hours — it's more valuable than late-night studying\n\n"
            "**During the Exam**\n"
            "- Read all questions before starting\n"
            "- Tackle easy questions first to build confidence\n"
            "- Manage your time — don't get stuck on one question\n"
            "- Show your work for partial credit\n"
            "- Review your answers if time allows\n\n"
            "**After the Exam**\n"
            "- Reflect on what worked and what didn't\n"
            "- Avoid post-exam stress — it's done! 🎉"
        ),
    },
    "productivity_tips": {
        "patterns": [
            r"\b(productivity tips?|focus tips?|how to focus|time management|be more productive|stay focused)\b",
        ],
        "response": (
            "## ⚡ Productivity & Focus Tips\n\n"
            "**Environment**\n"
            "- Dedicate a specific space only for studying\n"
            "- Keep your workspace clean and organized\n"
            "- Use natural light when possible\n\n"
            "**Digital Discipline**\n"
            "- Use apps like Forest or Cold Turkey to block distractions\n"
            "- Turn off notifications during study sessions\n"
            "- Keep your phone in another room\n\n"
            "**Time Management**\n"
            "- Plan your day the night before\n"
            "- Use time-blocking: assign specific subjects to time slots\n"
            "- Prioritize with the Eisenhower Matrix (urgent vs important)\n\n"
            "**Energy Management**\n"
            "- Exercise regularly — it boosts cognitive function\n"
            "- Eat brain foods: nuts, blueberries, dark chocolate, fish\n"
            "- Stay hydrated — dehydration impairs concentration\n\n"
            "**Mindset**\n"
            "- Break big tasks into small, actionable steps\n"
            "- Celebrate small wins to maintain motivation\n"
            "- Use positive self-talk and growth mindset"
        ),
    },
    "about": {
        "patterns": [
            r"\b(about|who are you|what are you|tell me about yourself|introduce yourself|your name)\b",
        ],
        "response": (
            "## 🤖 About StudyBot\n\n"
            "I'm **StudyBot**, an AI-powered study assistant built to help students learn more effectively.\n\n"
            "**What powers me:**\n"
            "- 🧠 **AI Engine**: HuggingFace SmolLM2-360M-Instruct for intelligent answers\n"
            "- 📄 **PDF Analysis**: TF-IDF retrieval for document Q&A\n"
            "- 💬 **Rule Engine**: Instant responses for common study queries\n"
            "- 🗄️ **Memory**: SQLite database stores your full conversation history\n\n"
            "**I can help with:**\n"
            "- Any academic subject or concept\n"
            "- Programming and computer science\n"
            "- Analyzing uploaded PDF documents\n"
            "- Study strategies and exam preparation\n\n"
            "*I run completely locally — no internet required, no data sent anywhere.*"
        ),
    },
}


def get_rule_response(message: str) -> Optional[str]:
    """Check if message matches any rule and return predefined response."""
    text = message.strip().lower()
    for rule_name, rule_data in RULES.items():
        for pattern in rule_data["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return rule_data["response"]
    return None
