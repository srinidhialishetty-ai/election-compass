import json
import os
import re
from datetime import datetime

try:
    import google.generativeai as genai
except ImportError:
    genai = None
import requests
from flask import Flask, jsonify, render_template, request, session

if genai:
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-pro")
else:
    model = None


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "election-compass-dev-secret")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["GOOGLE_ANALYTICS_ID"] = os.getenv("GOOGLE_ANALYTICS_ID", "").strip()

    TOPIC_GUIDES = {
        "overview": {
            "title": "Election Overview",
            "summary": (
                "An election usually moves through preparation, registration, public information, "
                "voting, counting, and the confirmation of results."
            ),
            "details": [
                "Preparation sets the rules, dates, and logistics for the election.",
                "Registration and eligibility checks help confirm who can vote.",
                "Before voting day, voters receive information about candidates, polling, or ballot options.",
                "On voting day, ballots are cast through the approved process.",
                "After voting ends, ballots are counted and results are reported, then officially confirmed.",
            ],
            "timeline": "Start with preparation, then registration, then public information, then voting day, then counting and official results.",
            "simple": "Think of it as a guided path: get ready, confirm who can vote, cast ballots, count them, and then publish the result.",
            "suggestions": [
                "Explain the stages one by one",
                "Show me the election timeline",
                "What happens on voting day?",
                "Give me a quick recap",
            ],
        },
        "stages": {
            "title": "Process Stages",
            "summary": (
                "The election process is easier to understand when it is broken into a few clear stages."
            ),
            "details": [
                "Preparation: election authorities announce the process and organize logistics.",
                "Registration and eligibility: people confirm whether they can participate and what requirements apply.",
                "Campaign or information phase: voters learn about choices and official notices.",
                "Voting day: ballots are cast through the approved method.",
                "Counting and reporting: ballots are reviewed and results are shared.",
                "Post-election outcome: final certification or official confirmation takes place.",
            ],
            "timeline": "The stages usually move in order and each one prepares the next stage to happen smoothly.",
            "simple": "The stages are like chapters in a guide, each explaining one part of how an election works.",
            "suggestions": [
                "Explain registration basics",
                "Show me the timeline format",
                "What happens after votes are cast?",
                "Explain simply",
            ],
        },
        "timeline": {
            "title": "Election Timeline",
            "summary": (
                "Election timelines vary by place, but the order usually stays similar even when dates change."
            ),
            "details": [
                "Early phase: authorities announce the election and key guidance.",
                "Registration checkpoint: eligible voters confirm their information before deadlines.",
                "Pre-voting phase: official notices, candidate information, and preparation continue.",
                "Voting day: ballots are cast.",
                "Post-voting period: ballots are counted, checked, and results are reported.",
                "Final phase: official confirmation or certification is completed.",
            ],
            "timeline": (
                "Preparation -> Registration checkpoint -> Public information phase -> Voting day -> Counting and reporting -> Official confirmation."
            ),
            "simple": "The easiest way to read the timeline is before voting, on voting day, and after voting.",
            "suggestions": [
                "Make that simpler",
                "Explain voting day next",
                "Why are there multiple stages?",
                "Give me the full process overview",
            ],
        },
        "registration": {
            "title": "Registration Basics",
            "summary": (
                "Registration and eligibility are the preparation steps that help determine who can vote in a given election."
            ),
            "details": [
                "Rules vary by election authority, so exact requirements depend on official guidance.",
                "People often need to confirm identity, address, or other local eligibility details.",
                "Deadlines matter because registration usually closes before voting day.",
                "Understanding this stage early reduces confusion later in the process.",
            ],
            "timeline": "Registration usually happens before voting day and often before the final campaign period concludes.",
            "simple": "Registration is the step where a person checks whether they are allowed to vote and whether their information is correct.",
            "suggestions": [
                "What happens before voting day?",
                "Show me the process stages",
                "Explain like I'm new",
                "What should I learn after registration?",
            ],
        },
        "voting_day": {
            "title": "Voting Day",
            "summary": (
                "Voting day is the phase when eligible voters complete the actual act of voting through the official process."
            ),
            "details": [
                "A voter typically checks in, follows instructions, receives or accesses a ballot, and completes it.",
                "Some voters may use assistance options if that is allowed under local rules.",
                "The process is designed to help ballots be cast securely and recorded correctly.",
                "After the ballot is submitted, the process moves toward counting and reporting.",
            ],
            "timeline": "Voting day comes after preparation and registration, but before counting and official reporting.",
            "simple": "Voting day is the moment when people arrive, follow the process, cast a ballot, and finish their participation for that election.",
            "suggestions": [
                "What happens after voting day?",
                "Give me a quick recap",
                "Explain counting and results",
                "Show me the full timeline",
            ],
        },
        "results": {
            "title": "Counting & Results",
            "summary": (
                "After voting closes, ballots are counted, reviewed, and reported before results become official."
            ),
            "details": [
                "Preliminary updates may appear before final confirmation is complete.",
                "Verification steps can take additional time depending on the process.",
                "This stage helps explain why official results are not always immediate.",
                "The final outcome is usually confirmed through the relevant authority's process.",
            ],
            "timeline": "Counting begins after voting ends, then reporting and final confirmation follow.",
            "simple": "After people vote, the ballots still need to be counted carefully before the final result is confirmed.",
            "suggestions": [
                "Why can results take time?",
                "Explain the whole process simply",
                "Show me the timeline again",
                "Give me a stage-by-stage recap",
            ],
        },
        "faq": {
            "title": "Common Questions",
            "summary": (
                "Many questions come from uncertainty about order, timing, and what each election phase is meant to do."
            ),
            "details": [
                "The process has multiple stages because elections involve preparation, participation, and verification.",
                "What happens before voting day depends on registration, logistics, and public information.",
                "What happens after votes are cast involves counting, reporting, and confirmation.",
            ],
            "timeline": "FAQ topics usually map back to the timeline: before voting, voting day itself, and after voting.",
            "simple": "The biggest questions are usually about what comes next and why the process takes more than one day.",
            "suggestions": [
                "What is the election process?",
                "What happens before voting day?",
                "What happens after votes are cast?",
                "How do I understand the timeline more easily?",
            ],
        },
    }

    SUGGESTED_QUESTIONS = {
        "overview": [
            "Explain the stages one by one",
            "Show me the election timeline",
            "What happens on voting day?",
            "Give me a quick recap",
        ],
        "stages": [
            "Explain registration basics",
            "What happens before voting day?",
            "Explain counting and results",
            "Make it simpler",
        ],
        "timeline": [
            "What happens before voting day?",
            "What happens after voting?",
            "Explain the process stages",
            "Give me a quick recap",
        ],
        "registration": [
            "Explain the full process",
            "What happens on voting day?",
            "Show me the timeline",
            "Explain simply",
        ],
        "voting_day": [
            "What happens after voting?",
            "Explain counting and results",
            "How does the full process work?",
            "Give me a simpler explanation",
        ],
        "results": [
            "Why are there multiple stages?",
            "Show me the election timeline",
            "Explain the process simply",
            "Give me a recap",
        ],
        "faq": [
            "What is the election process?",
            "Why are there multiple stages?",
            "What happens before voting day?",
            "How can I understand the timeline more easily?",
        ],
    }

    SECTION_MAP = {
        "overview": "assistant",
        "stages": "process",
        "timeline": "timeline",
        "registration": "process",
        "voting_day": "process",
        "results": "timeline",
        "faq": "faq",
    }

    PROCESS_ORDER = ["overview", "registration", "stages", "voting_day", "results", "timeline"]

    def initialize_session_state() -> None:
        session.setdefault("current_topic", "overview")
        session.setdefault("mode", "quick")
        session.setdefault("style", "simple")
        session.setdefault("last_interaction_source", "manual")
        session.setdefault("history", [])
        session.setdefault("visited_topics", [])
        session.setdefault(
            "progress",
            {
                "started": True,
                "overview_learned": False,
                "stages_explored": False,
                "timeline_understood": False,
                "recap_completed": False,
            },
        )

    def keyword_match(text: str, words: list[str]) -> bool:
        return any(word in text for word in words)

    def classify_topic(question: str) -> str:
        text = (question or "").strip().lower()

        if not text:
            return session.get("current_topic", "overview")
        if keyword_match(text, ["timeline", "order", "sequence", "schedule", "when"]):
            return "timeline"
        if keyword_match(text, ["register", "registration", "eligible", "eligibility", "sign up"]):
            return "registration"
        if keyword_match(text, ["voting day", "polling", "poll", "ballot", "cast vote", "vote day"]):
            return "voting_day"
        if keyword_match(text, ["count", "results", "after voting", "after votes", "certify", "reporting"]):
            return "results"
        if keyword_match(text, ["stage", "steps", "step-by-step", "one by one", "process stage"]):
            return "stages"
        if keyword_match(text, ["faq", "question", "confused", "don't understand", "new", "simple", "explain simply"]):
            return "faq"
        return "overview"

    def mark_topic_visit(topic: str) -> tuple[dict, list[str]]:
        progress = session.get("progress", {}).copy()
        visited_topics = list(session.get("visited_topics", []))

        if topic not in visited_topics:
            visited_topics.append(topic)

        if topic == "overview":
            progress["overview_learned"] = True
        if topic in {"stages", "registration", "voting_day"}:
            progress["stages_explored"] = True
        if topic in {"timeline", "results"}:
            progress["timeline_understood"] = True

        return progress, visited_topics

    def suggest_next_topics(topic: str, visited_topics: list[str]) -> list[str]:
        topic_routes = {
            "overview": ["stages", "timeline", "registration", "results"],
            "stages": ["registration", "voting_day", "timeline", "results"],
            "timeline": ["stages", "voting_day", "results", "overview"],
            "registration": ["stages", "voting_day", "timeline", "results"],
            "voting_day": ["results", "timeline", "stages", "overview"],
            "results": ["timeline", "overview", "stages", "faq"],
            "faq": ["overview", "timeline", "stages", "results"],
        }
        next_topics = topic_routes.get(topic, ["overview", "stages", "timeline", "results"])
        unvisited = [item for item in next_topics if item not in visited_topics]
        ordered = unvisited + [item for item in next_topics if item in visited_topics]
        return ordered[:4]

    def build_suggestions(
        topic: str,
        progress: dict,
        visited_topics: list[str],
        last_topic: str | None,
    ) -> list[str]:
        suggestion_bank = {
            "overview": {
                "stages": "Walk me through the stages one by one",
                "timeline": "Show me the election timeline next",
                "registration": "Explain registration and eligibility",
                "results": "What happens after votes are cast?",
                "faq": "Give me a quick recap",
            },
            "stages": {
                "registration": "Explain the registration stage",
                "voting_day": "What happens on voting day?",
                "timeline": "Place these stages on a timeline",
                "results": "What follows after voting day?",
                "overview": "Give me the overall process again",
            },
            "timeline": {
                "stages": "Break that timeline into stages",
                "voting_day": "Focus only on voting day",
                "results": "What happens after voting closes?",
                "overview": "Give me the big-picture version",
                "faq": "Summarize this more simply",
            },
            "registration": {
                "stages": "What stage comes after registration?",
                "voting_day": "Explain what happens on voting day",
                "timeline": "Where does registration fit in the timeline?",
                "results": "What happens after voting?",
                "overview": "Return to the full process overview",
            },
            "voting_day": {
                "results": "Explain counting and results next",
                "timeline": "Show where voting day sits in the timeline",
                "stages": "What stage comes after voting day?",
                "overview": "Summarize the full process for me",
                "faq": "Make this simpler",
            },
            "results": {
                "timeline": "Show the full timeline again",
                "overview": "Return to the big-picture explanation",
                "stages": "Which stage leads into results?",
                "faq": "Why can results take time?",
                "registration": "Start earlier in the process",
            },
            "faq": {
                "overview": "What is the election process?",
                "timeline": "How do I understand the timeline more easily?",
                "stages": "Why are there multiple stages?",
                "results": "What happens after votes are cast?",
                "registration": "What happens before voting day?",
            },
        }

        route_order = suggest_next_topics(topic, visited_topics)
        topic_map = suggestion_bank.get(topic, suggestion_bank["overview"])
        suggestions = [topic_map[item] for item in route_order if item in topic_map]

        if last_topic and last_topic != topic:
            revisit_prompt = f"Compare this with {TOPIC_GUIDES[last_topic]['title'].lower()}"
            if revisit_prompt not in suggestions:
                suggestions.append(revisit_prompt)

        if progress.get("recap_completed") is False:
            recap_prompt = "Give me a short recap"
            if recap_prompt not in suggestions:
                suggestions.append(recap_prompt)

        unique = []
        for item in suggestions:
            if item not in unique:
                unique.append(item)
            if len(unique) == 4:
                break
        return unique

    def build_simple_response(topic: str) -> str:
        guide = TOPIC_GUIDES.get(topic, TOPIC_GUIDES["overview"])
        return (
            f"{guide['simple']} "
            f"{guide['summary']} "
            "Each stage helps keep the process organized and easier to follow."
        )

    def build_detailed_response(topic: str) -> str:
        guide = TOPIC_GUIDES.get(topic, TOPIC_GUIDES["overview"])
        details = guide["details"]
        first = (
            f"{guide['summary']} It is not limited to one day; it includes preparation, eligibility checks, "
            "public information, voting, counting, and official confirmation."
        )
        second = " ".join(details[:4])
        third = (
            "This sequence helps the process stay organized, transparent, and understandable for citizens. "
            "Exact dates, deadlines, and requirements can still vary by official election authority."
        )
        return f"{first}\n\n{second}\n\n{third}"

    def build_step_response(topic: str) -> str:
        guide = TOPIC_GUIDES.get(topic, TOPIC_GUIDES["overview"])
        return "\n".join(
            f"{index + 1}. {detail}"
            for index, detail in enumerate(guide["details"])
        )

    def build_local_answer(
        question: str,
        topic: str,
        mode: str,
        style: str,
        interaction_source: str,
        last_topic: str | None,
    ) -> dict:
        guide = TOPIC_GUIDES.get(topic, TOPIC_GUIDES["overview"])
        question_lc = (question or "").lower()
        progress, visited_topics = mark_topic_visit(topic)

        if "recap" in question_lc:
            progress["recap_completed"] = True

        effective_style = style
        if interaction_source == "explain_new":
            effective_style = "simple"

        is_step_by_step = mode == "step"

        if effective_style == "timeline":
            answer = f"{guide['title']} in timeline order:"
            bullets = [
                "Preparation establishes the rules, timeline, and logistics.",
                "Registration and eligibility checks happen before participation.",
                "Voting day follows the public information phase.",
                "Counting and reporting continue after ballots are cast.",
            ]
            clarification = guide["timeline"]
        elif is_step_by_step:
            answer = build_step_response(topic)
            bullets = []
            clarification = ""
        elif effective_style == "detailed":
            answer = build_detailed_response(topic)
            bullets = []
            clarification = ""
        else:
            answer = build_simple_response(topic)
            bullets = []
            clarification = ""

        if interaction_source == "suggestion" and last_topic and last_topic != topic:
            clarification += f" This follows naturally from your previous question about {TOPIC_GUIDES[last_topic]['title'].lower()}."

        if "confused" in question_lc:
            if is_step_by_step:
                answer = build_step_response(topic)
            elif effective_style == "detailed":
                answer = build_detailed_response(topic)
            else:
                answer = (
                    "In the simplest terms, elections move from preparation to voting and then to counting and confirmation. "
                    "Each part has a clear job, so the process is easier to understand. "
                    "Exact rules can vary by official election authority."
                )
            bullets = []
            clarification = ""

        example = None
        if topic == "timeline":
            example = "Public notice -> registration checkpoint -> voting day -> counting -> official reporting."
        elif topic == "voting_day":
            example = "A voter arrives, checks in, follows instructions, and then submits a ballot."
        elif topic == "results":
            example = "Early reports may appear before final confirmation is complete."

        suggestions = build_suggestions(topic, progress, visited_topics, last_topic)
        section = SECTION_MAP.get(topic, "assistant")

        return {
            "heading": guide["title"],
            "answer": answer,
            "bullets": bullets,
            "clarification": clarification,
            "example": example,
            "topic": topic,
            "recommended_section": section,
            "suggestions": suggestions,
            "progress": progress,
            "visited_topics": visited_topics,
            "suggested_next_topic": suggest_next_topics(topic, visited_topics)[0] if suggest_next_topics(topic, visited_topics) else topic,
            "used_fallback": True,
            "source": "local_fallback",
        }

    def build_system_prompt() -> str:
        return (
            "You are Election Compass, a neutral election process education assistant. "
            "Your role is to explain how elections generally work in a clear, nonpartisan, educational way. "
            "Do not persuade, campaign, or give party-specific guidance. "
            "Keep explanations accurate at a general civic-process level and avoid overclaiming exact local rules or live dates. "
            "When relevant, note that exact dates and requirements depend on official election authorities. "
            "Return valid JSON only with this schema: "
            '{"heading":"string","answer":"string","bullets":["string"],"clarification":"string","example":"string or empty",'
            '"topic":"one of overview|stages|timeline|registration|voting_day|results|faq",'
            '"recommended_section":"assistant or process or timeline or faq or recap",'
            '"suggestions":["string","string","string","string"]}.'
        )

    def build_user_prompt(question: str, topic: str, mode: str, style: str, interaction_source: str) -> str:
        history = session.get("history", [])[-3:]
        history_text = "\n".join(
            f"User: {entry['question']}\nAssistant topic: {entry['topic']}"
            for entry in history
            if entry.get("question")
        ) or "No previous history."

        return (
            f"Current topic focus: {topic}\n"
            f"Learning mode: {mode}\n"
            f"Response style: {style}\n"
            f"Interaction source: {interaction_source}\n"
            f"Recent session context:\n{history_text}\n\n"
            f"User question: {question}\n\n"
            "Instructions:\n"
            "- Make the answer readable and useful for first-time learners.\n"
            "- Return a short heading, an answer string, optional bullets, a short clarification, and an optional example.\n"
            "- If response style is simple, put 2 to 3 short beginner-friendly sentences in answer, with no numbered steps and no bullets.\n"
            "- If response style is detailed, put 2 to 3 proper paragraphs in answer, with no numbered steps and no bullets.\n"
            "- If learning mode is step, put only a numbered list in answer. Keep each item short. Do not include extra paragraphs or bullets.\n"
            "- If response style is timeline, explain phases in chronological order and bullets are allowed.\n"
            "- If the interaction source is chip or suggestion, keep the explanation concise.\n"
            "- If the interaction source is manual, allow slightly more detail.\n"
            "- If the user sounds confused, simplify first.\n"
            "- If the user asks about timeline, explain phases in order.\n"
            "- If the user asks about voting day, focus on that phase only.\n"
            "- If the user asks what happens after voting, focus on counting and results.\n"
            "- Provide 4 concrete follow-up suggestions.\n"
            "- Keep the tone calm, civic, neutral, and educational.\n"
            "- Mention that exact dates or requirements may vary by official election authority when helpful."
        )

    def call_gemini(question: str, topic: str, mode: str, style: str, interaction_source: str) -> dict:
        if not os.getenv("GEMINI_API_KEY") or model is None:
            raise RuntimeError("Missing GEMINI_API_KEY")

        user_input = question
        prompt = f"""
Explain the election process topic clearly.

User question: {user_input}

Response style: {style}

Give structured, clear explanation.
"""
        response = model.generate_content(prompt)
        response_text = str(getattr(response, "text", "")).strip()
        if not response_text:
            raise ValueError("Gemini response was empty")

        progress, visited_topics = mark_topic_visit(topic)
        suggestions = SUGGESTED_QUESTIONS.get(topic, SUGGESTED_QUESTIONS["overview"])[:4]
        result = {
            "heading": TOPIC_GUIDES[topic]["title"],
            "answer": response_text,
            "response": response_text,
            "bullets": [],
            "clarification": "Exact dates, deadlines, and requirements can vary by official election authority.",
            "example": None,
            "topic": topic,
            "recommended_section": SECTION_MAP.get(topic, "assistant"),
            "suggestions": suggestions,
            "progress": progress,
            "visited_topics": visited_topics,
            "suggested_next_topic": get_suggested_next_topic(visited_topics),
            "used_fallback": False,
            "source": "gemini",
        }
        return result

    def extract_text_from_gemini(payload: dict) -> str:
        candidates = payload.get("candidates") or []
        if not candidates:
            raise ValueError("No Gemini candidates returned")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise ValueError("Gemini response did not contain text")
        return "".join(text_parts)

    def parse_model_json(text: str, mode: str, style: str) -> dict | None:
        cleaned = text.strip()
        try:
            data = json.loads(cleaned)
            return normalize_model_response(data, mode, style)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
                return normalize_model_response(data, mode, style)
            except json.JSONDecodeError:
                return None

    def normalize_model_response(data: dict, mode: str, style: str) -> dict:
        topic = data.get("topic", "overview")
        if topic not in TOPIC_GUIDES:
            topic = "overview"

        progress, visited_topics = mark_topic_visit(topic)
        suggested = data.get("suggestions") or SUGGESTED_QUESTIONS.get(topic, [])
        suggestions = [str(item).strip() for item in suggested if str(item).strip()][:4]
        while len(suggestions) < 4:
            for fallback in SUGGESTED_QUESTIONS.get(topic, []):
                if fallback not in suggestions:
                    suggestions.append(fallback)
                if len(suggestions) == 4:
                    break

        section = data.get("recommended_section", SECTION_MAP.get(topic, "assistant"))
        if section not in {"assistant", "process", "timeline", "faq", "recap"}:
            section = SECTION_MAP.get(topic, "assistant")

        answer = str(data.get("answer", "")).strip()
        if not answer:
            raise ValueError("Model response missing answer")

        if "recap" in answer.lower() or "recap" in str(data.get("heading", "")).lower():
            progress["recap_completed"] = True

        heading = str(data.get("heading", TOPIC_GUIDES[topic]["title"])).strip() or TOPIC_GUIDES[topic]["title"]
        bullets = [str(item).strip() for item in (data.get("bullets") or []) if str(item).strip()][:4]
        if not bullets:
            bullets = TOPIC_GUIDES[topic]["details"][:3]

        clarification = str(data.get("clarification", TOPIC_GUIDES[topic]["simple"])).strip() or TOPIC_GUIDES[topic]["simple"]
        example = normalize_example_text(data.get("example", ""))
        answer, bullets, clarification = apply_response_style_shape(
            topic,
            answer,
            bullets,
            clarification,
            mode,
            style,
        )

        return {
            "heading": heading,
            "answer": answer,
            "bullets": bullets,
            "clarification": clarification,
            "example": example,
            "topic": topic,
            "recommended_section": section,
            "suggestions": suggestions[:4],
            "progress": progress,
            "visited_topics": visited_topics,
            "suggested_next_topic": suggest_next_topics(topic, visited_topics)[0] if suggest_next_topics(topic, visited_topics) else topic,
            "used_fallback": False,
            "source": "gemini",
        }

    def apply_response_style_shape(
        topic: str,
        answer: str,
        bullets: list[str],
        clarification: str,
        mode: str,
        style: str,
    ) -> tuple[str, list[str], str]:
        if style == "timeline":
            return answer, bullets, clarification

        if mode == "step":
            source_items = bullets or [
                line.strip()
                for line in re.split(r"\n+", answer)
                if line.strip()
            ] or TOPIC_GUIDES[topic]["details"]
            clean_items = [
                re.sub(r"^(?:step\s*)?\d+[\).:\-]\s*", "", item, flags=re.IGNORECASE).strip()
                for item in source_items
            ]
            numbered = "\n".join(
                f"{index + 1}. {item}"
                for index, item in enumerate(clean_items)
                if item
            )
            return numbered, [], ""

        if style == "detailed":
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", answer) if part.strip()]
            if len(paragraphs) < 2:
                paragraphs = [build_detailed_response(topic)]
            return "\n\n".join(paragraphs[:3]), [], ""

        return build_simple_response(topic), [], ""

    def normalize_example_text(example: object) -> str | None:
        cleaned = str(example or "").strip()
        cleaned = re.sub(r"^\s*example(?:\s+sequence)?\s*:\s*", "", cleaned, flags=re.IGNORECASE)
        return cleaned or None

    FAQ_ITEMS = [
        {
            "question": "What is the election process?",
            "answer": "It is the overall sequence that helps an election move from preparation and voter participation to counting and official results.",
            "topic": "overview",
        },
        {
            "question": "Why are there multiple stages?",
            "answer": "Different stages help organize preparation, voting, and verification so the process is clear and orderly.",
            "topic": "stages",
        },
        {
            "question": "What happens before voting day?",
            "answer": "Before voting day, people often check registration, review official information, and prepare to participate.",
            "topic": "registration",
        },
        {
            "question": "What happens after votes are cast?",
            "answer": "After voting ends, ballots are counted, results are reported, and official confirmation follows.",
            "topic": "results",
        },
        {
            "question": "How can I understand the timeline more easily?",
            "answer": "Think of it in three parts: before voting, voting day itself, and what happens after ballots are cast.",
            "topic": "timeline",
        },
    ]

    def render_page(template_name: str, active_page: str, **context):
        initialize_session_state()
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%b %d, %Y")
        return render_template(
            template_name,
            today=today,
            active_page=active_page,
            google_analytics_id=app.config["GOOGLE_ANALYTICS_ID"],
            **context,
        )

    @app.route("/")
    def index():
        return render_page("index.html", "home")

    @app.route("/assistant")
    def assistant_page():
        initial_question = request.args.get("question", "").strip()
        initial_topic = request.args.get("topic", "").strip().lower()
        if initial_topic not in TOPIC_GUIDES:
            initial_topic = session.get("current_topic", "overview")
        return render_page(
            "assistant.html",
            "assistant",
            initial_question=initial_question,
            initial_topic=initial_topic,
        )

    @app.route("/paths")
    def paths_page():
        return render_page("paths.html", "paths")

    @app.route("/stages")
    def stages_page():
        return render_page("stages.html", "stages")

    @app.route("/timeline")
    def timeline_page():
        return render_page("timeline.html", "timeline")

    @app.route("/faq")
    def faq_page():
        return render_page("faq.html", "faq", faq_items=FAQ_ITEMS)

    @app.route("/ask", methods=["POST"])
    @app.route("/api/assistant", methods=["POST"])
    def assistant_api():
        initialize_session_state()

        payload = request.get_json(silent=True) or {}
        question = str(payload.get("question", "")).strip()
        mode = str(payload.get("mode", session.get("mode", "quick"))).strip().lower()
        style = str(payload.get("style", session.get("style", "simple"))).strip().lower()
        requested_topic = str(payload.get("topic", "")).strip().lower()
        context_topic = str(payload.get("context", "")).strip().lower()
        explain_like_new = bool(payload.get("explain_like_new"))
        interaction_source = str(payload.get("interaction_source", session.get("last_interaction_source", "manual"))).strip().lower()

        mode_aliases = {
            "step-by-step": "step",
            "step_by_step": "step",
            "step by step": "step",
        }
        style_aliases = {
            "clear": "simple",
            "clear explanation": "simple",
            "step-by-step": "detailed",
            "step_by_step": "detailed",
            "step by step": "detailed",
        }
        mode = mode_aliases.get(mode, mode)
        style = style_aliases.get(style, style)

        if mode not in {"quick", "step", "ask"}:
            mode = "quick"
        if style not in {"simple", "detailed", "timeline"}:
            style = "simple"
        if explain_like_new:
            style = "simple"
            interaction_source = "explain_new"
        if interaction_source not in {"manual", "chip", "suggestion", "explain_new"}:
            interaction_source = "manual"

        if not question:
            return (
                jsonify(
                    {
                        "heading": "Start here",
                        "answer": "The assistant can explain stages, timelines, voting day, results, and common civic questions.",
                        "bullets": [
                            "Ask for the full election overview.",
                            "Choose one stage such as registration or voting day.",
                            "Request a timeline or a short recap.",
                        ],
                        "clarification": "Select one of the suggested prompts below or type your own question to begin.",
                        "example": None,
                        "topic": session.get("current_topic", "overview"),
                        "recommended_section": "assistant",
                        "suggestions": [
                            "What is the election process?",
                            "Show me the election timeline",
                            "Explain voting day",
                        ],
                        "progress": session.get("progress"),
                        "visited_topics": session.get("visited_topics", []),
                        "suggested_next_topic": session.get("current_topic", "overview"),
                        "used_fallback": True,
                        "source": "empty_state",
                        "error": "empty_question",
                    }
                ),
                400,
            )

        topic = requested_topic if requested_topic in TOPIC_GUIDES else context_topic if context_topic in TOPIC_GUIDES else classify_topic(question)
        if topic == "faq" and requested_topic in {"overview", "stages", "timeline", "registration", "voting_day", "results"}:
            topic = requested_topic

        session["mode"] = mode
        session["style"] = style
        session["current_topic"] = topic
        session["last_interaction_source"] = interaction_source
        last_topic = history[-1]["topic"] if (history := session.get("history", [])) else None

        try:
            result = call_gemini(question, topic, mode, style, interaction_source)
        except Exception:
            result = build_local_answer(question, topic, mode, style, interaction_source, last_topic)
            result["response"] = result.get("answer", "")

        session["progress"] = result["progress"]
        history.append(
            {
                "question": question,
                "topic": result["topic"],
                "mode": mode,
            }
        )
        session["history"] = history[-8:]
        session["visited_topics"] = result.get("visited_topics", session.get("visited_topics", []))

        return jsonify(result)

    @app.route("/api/state")
    def state():
        initialize_session_state()
        return jsonify(
            {
                "current_topic": session.get("current_topic", "overview"),
                "mode": session.get("mode", "quick"),
                "style": session.get("style", "simple"),
                "progress": session.get("progress"),
                "visited_topics": session.get("visited_topics", []),
            }
        )

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.route("/favicon.ico")
    def favicon():
        return ("", 204)

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
