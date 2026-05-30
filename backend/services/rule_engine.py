import re
from typing import Optional


RULES: list[dict] = [
    {
        "patterns": [r"\bhello\b", r"\bhi\b", r"\bhey\b", r"\bgreetings\b"],
        "response": (
            "👋 Hello! I'm **StudyMate AI**, your intelligent study companion.\n\n"
            "I can help you with:\n"
            "- 💬 **Answering questions** about any topic\n"
            "- 📄 **PDF Q&A** — upload a PDF and ask questions about it\n"
            "- 📚 **Study tips** to improve your learning\n"
            "- 🎯 **Exam strategies** to boost your performance\n\n"
            "What would you like to explore today?"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bgood\s*morning\b"],
        "response": (
            "☀️ Good morning! Ready to make today productive?\n\n"
            "**Morning Study Tip:** Your brain is sharpest in the morning — "
            "tackle your hardest subjects first. Save lighter review for the afternoon.\n\n"
            "What are you studying today?"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bgood\s*afternoon\b"],
        "response": (
            "🌤️ Good afternoon! Hope your day is going well.\n\n"
            "**Afternoon Tip:** This is a great time for group study or reviewing notes from the morning. "
            "Take a 10-minute break if you've been studying for over an hour.\n\n"
            "What can I help you with?"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bgood\s*evening\b", r"\bgood\s*night\b"],
        "response": (
            "🌙 Good evening! Winding down with some studying?\n\n"
            "**Evening Tip:** Avoid cramming new material before bed. "
            "Instead, review what you already know — sleep consolidates memory!\n\n"
            "What would you like to review?"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bhelp\b", r"\bwhat can you do\b", r"\bcommands\b", r"\bfeatures\b"],
        "response": (
            "🤖 **StudyMate AI — Help Center**\n\n"
            "**Available Commands:**\n"
            "- `hello` / `hi` — Greet me\n"
            "- `study tips` — Get evidence-based study strategies\n"
            "- `exam tips` — Get exam preparation advice\n"
            "- `productivity tips` — Boost your workflow\n"
            "- `about` — Learn about StudyMate AI\n\n"
            "**AI Features:**\n"
            "- Ask me **any question** — I'll answer using AI\n"
            "- **Upload a PDF** (top-right button) then ask questions about it\n"
            "- All conversations are **saved** in the sidebar\n\n"
            "**Tips:**\n"
            "- Be specific in your questions for better answers\n"
            "- Upload lecture slides or textbook chapters for instant Q&A"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bstudy\s*tip[s]?\b", r"\bhow\s*to\s*study\b", r"\blearn\s*(better|faster|effectively)\b"],
        "response": (
            "📚 **Evidence-Based Study Tips**\n\n"
            "**1. Active Recall**\nDon't just re-read — test yourself. Close the book and try to recall key points. "
            "This is the single most effective study technique.\n\n"
            "**2. Spaced Repetition**\nStudy in sessions spread over days, not marathon sessions. "
            "Review material at increasing intervals (1 day → 3 days → 1 week).\n\n"
            "**3. The Pomodoro Technique**\n25 minutes focused study → 5 minute break. "
            "After 4 rounds, take a 20-minute break.\n\n"
            "**4. Interleaving**\nMix different subjects or problem types in one session instead of blocking one topic.\n\n"
            "**5. The Feynman Technique**\nExplain the concept in simple words as if teaching a child. "
            "Gaps in your explanation reveal gaps in your understanding.\n\n"
            "**6. Eliminate Distractions**\nPhone in another room, website blockers enabled, "
            "quiet environment or instrumental music only.\n\n"
            "Want me to elaborate on any of these?"
        ),
        "type": "rule",
    },
    {
        "patterns": [
            r"\bexam\s*tip[s]?\b",
            r"\btest\s*tip[s]?\b",
            r"\bexam\s*prep\b",
            r"\bprepare\s*for\s*(exam|test)\b",
            r"\bexam\s*strateg\w*\b",
        ],
        "response": (
            "🎯 **Exam Preparation Strategies**\n\n"
            "**Before the Exam:**\n"
            "- 📅 Create a study schedule at least 2 weeks before\n"
            "- 📝 Summarize each topic in your own words\n"
            "- ✅ Practice with past papers under timed conditions\n"
            "- 💤 Get 7–9 hours of sleep the night before\n"
            "- 🍳 Eat a proper breakfast — glucose fuels your brain\n\n"
            "**During the Exam:**\n"
            "- ⏱️ Skim all questions first, then plan your time\n"
            "- ✔️ Answer easy questions first to build confidence\n"
            "- 🔍 Read each question twice before answering\n"
            "- ✏️ For essays: outline before writing\n"
            "- 🔄 Leave time to review your answers\n\n"
            "**Mindset:**\n"
            "- Anxiety is normal — controlled breathing helps\n"
            "- Focus on what you know, not what you don't\n\n"
            "Good luck! You've got this. 💪"
        ),
        "type": "rule",
    },
    {
        "patterns": [
            r"\bproductivity\s*tip[s]?\b",
            r"\btime\s*management\b",
            r"\bfocus\b",
            r"\bconcentrat\w+\b",
            r"\bproductive\b",
        ],
        "response": (
            "⚡ **Productivity & Focus Tips**\n\n"
            "**Planning:**\n"
            "- 📋 Plan tomorrow's tasks tonight — reduces decision fatigue\n"
            "- 🎯 Pick your 3 Most Important Tasks (MITs) each day\n"
            "- ⏰ Time-block your calendar with study sessions\n\n"
            "**Environment:**\n"
            "- 🔕 Put your phone on Do Not Disturb\n"
            "- 🎵 Try brown noise or lo-fi music for focus\n"
            "- 💡 Ensure adequate lighting — dim rooms cause fatigue\n"
            "- 🌡️ Keep the room slightly cool (18–20°C is optimal)\n\n"
            "**Habits:**\n"
            "- 🚶 Take a 10-minute walk between heavy study sessions\n"
            "- 💧 Stay hydrated — even mild dehydration impairs cognition\n"
            "- 🏋️ Exercise 3–4 times per week — it boosts memory formation\n"
            "- 🧘 5 minutes of mindfulness before studying sharpens focus\n\n"
            "**Digital:**\n"
            "- Use apps like Forest, Cold Turkey, or Freedom to block distractions\n"
            "- Turn off all notifications during study blocks"
        ),
        "type": "rule",
    },
    {
        "patterns": [
            r"\babout\b",
            r"\bwho\s*are\s*you\b",
            r"\bwhat\s*are\s*you\b",
            r"\btell\s*me\s*about\s*yourself\b",
        ],
        "response": (
            "🎓 **About StudyMate AI**\n\n"
            "I'm **StudyMate AI** — an intelligent study assistant designed to supercharge your learning.\n\n"
            "**How I Work:**\n"
            "1. **Rule Engine** — Instant, curated responses for common study queries\n"
            "2. **AI Layer** — Powered by Hugging Face Transformers for open-ended questions\n"
            "3. **PDF Q&A** — Upload any PDF; I'll extract, embed, and answer questions from it\n\n"
            "**Tech Stack:**\n"
            "- 🐍 Python + FastAPI backend\n"
            "- 🤗 Hugging Face Transformers (Flan-T5)\n"
            "- 📐 Sentence Transformers for semantic search\n"
            "- 🗄️ SQLite database for persistent history\n"
            "- 🎨 Vanilla JS + CSS frontend\n\n"
            "**Built for:** Students, researchers, and lifelong learners.\n\n"
            "Ask me anything — let's learn together! 🚀"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bthank[s]?\b", r"\bthank\s*you\b", r"\bthanks\s*a\s*lot\b"],
        "response": (
            "😊 You're very welcome! Happy to help.\n\n"
            "Remember: **consistent small efforts compound into big results**. "
            "Keep up the great work with your studies!\n\n"
            "Is there anything else I can help you with?"
        ),
        "type": "rule",
    },
    {
        "patterns": [r"\bbye\b", r"\bgoodbye\b", r"\bsee\s*you\b", r"\bciao\b"],
        "response": (
            "👋 Goodbye! Great studying today.\n\n"
            "**Before you go:** Review your notes one more time — "
            "the last thing you review before sleeping tends to stick best.\n\n"
            "Come back anytime. Good luck! 🌟"
        ),
        "type": "rule",
    },
]


def match_rule(message: str) -> Optional[dict]:
    """Return the matching rule dict or None."""
    text = message.lower().strip()
    for rule in RULES:
        for pattern in rule["patterns"]:
            if re.search(pattern, text):
                return rule
    return None
