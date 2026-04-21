import json
import os
import re
from datetime import datetime

import requests
from flask import Flask, jsonify, render_template, request, session


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "election-compass-dev-secret")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

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

    def initialize_session_state() -> None:
        session.setdefault("current_topic", "overview")
        session.setdefault("mode", "quick")
        session.setdefault("style", "simple")
        session.setdefault("history", [])
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

    def build_local_answer(question: str, topic: str, mode: str, style: str) -> dict:
        guide = TOPIC_GUIDES.get(topic, TOPIC_GUIDES["overview"])
        progress = session.get("progress", {}).copy()
        question_lc = (question or "").lower()

        if "recap" in question_lc:
            progress["recap_completed"] = True

        if topic == "overview":
            progress["overview_learned"] = True
        if topic in {"stages", "registration", "voting_day"}:
            progress["stages_explored"] = True
        if topic in {"timeline", "results"}:
            progress["timeline_understood"] = True

        if style == "timeline":
            answer_body = guide["timeline"]
        elif style == "detailed" or mode == "step":
            answer_body = " ".join(guide["details"])
        elif "simple" in question_lc or style == "simple":
            answer_body = guide["simple"]
        else:
            answer_body = guide["summary"]

        intro = f"{guide['title']}: "
        answer = f"{intro}{answer_body}"

        if mode == "ask":
            answer += " If you want, you can follow up on a specific phase and I can stay focused on just that part."
        elif mode == "step":
            answer += " This is part of a step-by-step path, so the next useful move is to continue to the following stage."

        if "confused" in question_lc:
            answer = (
                "Here is the simplest version first: elections usually involve getting ready, confirming who can vote, "
                "voting, and then counting the ballots before results are made official. "
                + answer_body
            )

        suggestions = guide["suggestions"][:]
        section = SECTION_MAP.get(topic, "assistant")

        return {
            "answer": answer,
            "topic": topic,
            "recommended_section": section,
            "suggestions": suggestions,
            "progress": progress,
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
            '{"answer":"string","topic":"one of overview|stages|timeline|registration|voting_day|results|faq",'
            '"recommended_section":"assistant or process or timeline or faq or recap",'
            '"suggestions":["string","string","string","string"]}.'
        )

    def build_user_prompt(question: str, topic: str, mode: str, style: str) -> str:
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
            f"Recent session context:\n{history_text}\n\n"
            f"User question: {question}\n\n"
            "Instructions:\n"
            "- Make the answer readable and useful for first-time learners.\n"
            "- Prefer short paragraphs or a compact structured explanation.\n"
            "- If the user sounds confused, simplify first.\n"
            "- If the user asks about timeline, explain phases in order.\n"
            "- If the user asks about voting day, focus on that phase only.\n"
            "- If the user asks what happens after voting, focus on counting and results.\n"
            "- Provide 4 concrete follow-up suggestions.\n"
            "- Keep the tone calm, civic, neutral, and educational.\n"
            "- Mention that exact dates or requirements may vary by official election authority when helpful."
        )

    def call_gemini(question: str, topic: str, mode: str, style: str) -> dict:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-2.5-flash:generateContent"
        )
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
        payload = {
            "system_instruction": {
                "parts": [{"text": build_system_prompt()}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": build_user_prompt(question, topic, mode, style)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 900,
                "responseMimeType": "application/json",
            },
        }

        response = requests.post(endpoint, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        text = extract_text_from_gemini(data)
        parsed = parse_model_json(text)
        if not parsed:
            raise ValueError("Gemini response was not valid JSON")

        return parsed

    def extract_text_from_gemini(payload: dict) -> str:
        candidates = payload.get("candidates") or []
        if not candidates:
            raise ValueError("No Gemini candidates returned")

        parts = candidates[0].get("content", {}).get("parts", [])
        text_parts = [part.get("text", "") for part in parts if part.get("text")]
        if not text_parts:
            raise ValueError("Gemini response did not contain text")
        return "".join(text_parts)

    def parse_model_json(text: str) -> dict | None:
        cleaned = text.strip()
        try:
            data = json.loads(cleaned)
            return normalize_model_response(data)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                return None
            try:
                data = json.loads(match.group(0))
                return normalize_model_response(data)
            except json.JSONDecodeError:
                return None

    def normalize_model_response(data: dict) -> dict:
        topic = data.get("topic", "overview")
        if topic not in TOPIC_GUIDES:
            topic = "overview"

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

        progress = session.get("progress", {}).copy()
        if topic == "overview":
            progress["overview_learned"] = True
        if topic in {"stages", "registration", "voting_day"}:
            progress["stages_explored"] = True
        if topic in {"timeline", "results"}:
            progress["timeline_understood"] = True
        if "recap" in answer.lower():
            progress["recap_completed"] = True

        return {
            "answer": answer,
            "topic": topic,
            "recommended_section": section,
            "suggestions": suggestions,
            "progress": progress,
            "used_fallback": False,
            "source": "gemini",
        }

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
        today = datetime.utcnow().strftime("%b %d, %Y")
        return render_template(template_name, today=today, active_page=active_page, **context)

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

    @app.route("/api/assistant", methods=["POST"])
    def assistant_api():
        initialize_session_state()

        payload = request.get_json(silent=True) or {}
        question = str(payload.get("question", "")).strip()
        mode = str(payload.get("mode", session.get("mode", "quick"))).strip().lower()
        style = str(payload.get("style", session.get("style", "simple"))).strip().lower()
        requested_topic = str(payload.get("topic", "")).strip().lower()
        explain_like_new = bool(payload.get("explain_like_new"))

        if mode not in {"quick", "step", "ask"}:
            mode = "quick"
        if style not in {"simple", "detailed", "timeline"}:
            style = "simple"
        if explain_like_new:
            style = "simple"

        if not question:
            return (
                jsonify(
                    {
                        "answer": (
                            "Start with a short question such as “What is the election process?”, "
                            "“Explain voting day”, or “Show me the timeline.”"
                        ),
                        "topic": session.get("current_topic", "overview"),
                        "recommended_section": "assistant",
                        "suggestions": SUGGESTED_QUESTIONS["overview"],
                        "progress": session.get("progress"),
                        "used_fallback": True,
                        "source": "empty_state",
                        "error": "empty_question",
                    }
                ),
                400,
            )

        topic = requested_topic if requested_topic in TOPIC_GUIDES else classify_topic(question)
        if topic == "faq" and requested_topic in {"overview", "stages", "timeline", "registration", "voting_day", "results"}:
            topic = requested_topic

        session["mode"] = mode
        session["style"] = style
        session["current_topic"] = topic

        try:
            result = call_gemini(question, topic, mode, style)
        except Exception:
            result = build_local_answer(question, topic, mode, style)

        session["progress"] = result["progress"]
        history = session.get("history", [])
        history.append(
            {
                "question": question,
                "topic": result["topic"],
            }
        )
        session["history"] = history[-8:]

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
            }
        )

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})

    return app


app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
