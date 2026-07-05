"""Module 1 evaluator prompt and rubric definition."""

MODULE1_EVALUATOR_PROMPT_VERSION = "1.0.0"

MODULE1_RUBRIC_ITEMS = [
    {
        "key": "therapeutic_presence",
        "category": "Therapeutic Presence",
        "description": "Engaged, attentive, emotionally responsive presence that creates safety and connection.",
        "max_score": 5,
        "weight": 12,
        "observable_indicators": [
            "Responses match client emotional content",
            "Counselor remains engaged rather than scripted or task-focused",
            "Client appears safer and more open over time",
        ],
        "common_mistakes": [
            "Gathering information without emotional attunement",
            "Using generic responses that do not fit the client moment",
        ],
        "feedback_guidance": "Reference how the student's responses affected safety, connection, and openness.",
        "rating_anchors": {
            "5": "Fully engaged and attentive throughout; responses consistently match client emotional content; creates strong sense of safety and connection.",
            "4": "Generally attentive and emotionally present with only minor lapses.",
            "3": "Demonstrates engagement but occasionally shifts into task-focused or scripted responses.",
            "2": "Attention appears inconsistent; focus often shifts to gathering information rather than understanding the client.",
            "1": "Limited evidence of engagement or emotional attunement.",
        },
    },
    {
        "key": "empathy",
        "category": "Empathy",
        "description": "Communicates understanding of the client's emotions and experience.",
        "max_score": 5,
        "weight": 12,
        "observable_indicators": [
            "Validates emotional experience",
            "Names or reflects feelings accurately",
            "Empathy advances exploration rather than closing it down",
        ],
        "common_mistakes": [
            "Generic empathy without connection to the client's exact concern",
            "Missing emotional meaning beneath surface content",
        ],
        "feedback_guidance": "Identify whether empathic statements were specific, accurate, and growth-promoting.",
        "rating_anchors": {
            "5": "Consistently communicates deep understanding of the client's emotions and experiences; empathy advances exploration.",
            "4": "Frequently demonstrates understanding and validation of emotions.",
            "3": "Basic empathic responses are present but often remain surface-level.",
            "2": "Empathy is inconsistent, generic, or occasionally misses emotional meaning.",
            "1": "Little evidence of empathic understanding.",
        },
    },
    {
        "key": "reflection_skills",
        "category": "Reflection Skills",
        "description": "Uses reflections of content, feeling, meaning, and themes to promote insight.",
        "max_score": 5,
        "weight": 12,
        "observable_indicators": [
            "Reflects content accurately",
            "Reflects feelings and meaning",
            "Client expands rather than simply repeats information",
        ],
        "common_mistakes": [
            "Overusing simple paraphrase",
            "Reflecting inaccurately or too vaguely",
        ],
        "feedback_guidance": "Distinguish paraphrase from deeper feeling or meaning reflections.",
        "rating_anchors": {
            "5": "Reflections accurately capture feelings, meaning, and themes while promoting insight.",
            "4": "Uses reflections effectively and accurately throughout most of the interaction.",
            "3": "Uses some reflections but relies heavily on paraphrasing or repetition.",
            "2": "Reflections are infrequent, inaccurate, or overly simplistic.",
            "1": "Minimal use of reflective listening skills.",
        },
    },
    {
        "key": "rapport_building",
        "category": "Rapport Building",
        "description": "Builds trust, warmth, collaboration, and comfort.",
        "max_score": 5,
        "weight": 10,
        "observable_indicators": [
            "Warmth and genuineness",
            "Client becomes more comfortable sharing",
            "Counselor supports collaboration rather than interrogation",
        ],
        "common_mistakes": [
            "Mechanical connection",
            "Limited collaboration or warmth",
        ],
        "feedback_guidance": "Tie rapport feedback to client engagement changes when possible.",
        "rating_anchors": {
            "5": "Creates strong trust, warmth, and collaboration; client appears comfortable sharing openly.",
            "4": "Establishes a positive and supportive relationship.",
            "3": "Basic rapport is present but connection may feel somewhat mechanical.",
            "2": "Limited efforts to build connection or collaboration.",
            "1": "Rapport appears weak or underdeveloped.",
        },
    },
    {
        "key": "response_to_emotional_content",
        "category": "Response to Emotional Content",
        "description": "Recognizes emotional cues and helps the client explore feelings, meanings, and experiences.",
        "max_score": 5,
        "weight": 14,
        "observable_indicators": [
            "Identifies emotion, vulnerability, uncertainty, fear, shame, sadness, frustration, or excitement",
            "Responds to emotion before shifting topics",
            "Helps deepen emotional exploration",
        ],
        "common_mistakes": [
            "Redirecting to content after an emotional cue",
            "Asking another information-gathering question too quickly",
        ],
        "feedback_guidance": "Evaluate at least two emotional moments and whether the student deepened, stayed surface-level, redirected, or missed the cue.",
        "rating_anchors": {
            "5": "Consistently recognizes emotional cues and helps the client explore feelings, meanings, and experiences in greater depth. Frequently responds to emotion rather than shifting topics or gathering information.",
            "4": "Frequently identifies and responds to emotional content, allowing for meaningful exploration.",
            "3": "Recognizes obvious emotions but may miss opportunities to deepen exploration or focus primarily on content.",
            "2": "Occasionally acknowledges emotions but often redirects the conversation, asks another question, or moves away from emotional material too quickly.",
            "1": "Rarely identifies or responds to emotional content; emotional cues are consistently overlooked.",
        },
    },
    {
        "key": "pacing",
        "category": "Pacing",
        "description": "Allows emotional moments to develop without rushing, stalling, or problem-solving too early.",
        "max_score": 5,
        "weight": 10,
        "observable_indicators": [
            "Balanced flow of conversation",
            "Emotional moments are given room",
            "No premature advice or excessive speed",
        ],
        "common_mistakes": [
            "Moving too quickly after client emotion",
            "Letting the session stall without therapeutic purpose",
        ],
        "feedback_guidance": "Connect pacing to rapport and client engagement.",
        "rating_anchors": {
            "5": "Conversation flows naturally; counselor allows emotional moments to develop without rushing or stalling.",
            "4": "Pacing generally supports client exploration.",
            "3": "Some moments feel rushed or prolonged unnecessarily.",
            "2": "Frequently moves too quickly or too slowly, limiting exploration.",
            "1": "Pacing significantly disrupts the counseling process.",
        },
    },
    {
        "key": "question_balance",
        "category": "Question Balance",
        "description": "Balances questions with reflections, summaries, and empathic responses so the client leads exploration.",
        "max_score": 5,
        "weight": 10,
        "observable_indicators": [
            "Questions support exploration without dominating",
            "Reflections and empathy are used alongside questions",
            "Session does not feel interview-driven",
        ],
        "common_mistakes": [
            "Rapid-fire questions",
            "Overreliance on closed or information-gathering questions",
        ],
        "feedback_guidance": "Evaluate whether questions opened emotional exploration or narrowed it.",
        "rating_anchors": {
            "5": "Excellent balance of questions, reflections, summaries, and empathic responses; client leads much of the exploration.",
            "4": "Questions generally support exploration without dominating the session.",
            "3": "Moderate overreliance on questions is evident.",
            "2": "Session feels largely interview-driven with limited processing.",
            "1": "Excessive questioning significantly limits therapeutic depth.",
        },
    },
    {
        "key": "silence_tolerance",
        "category": "Silence Tolerance",
        "description": "Uses silence intentionally and comfortably to encourage reflection and emotional processing.",
        "max_score": 5,
        "weight": 10,
        "observable_indicators": [
            "Allows therapeutic pauses",
            "Does not fill silence prematurely",
            "Client uses space for deeper reflection",
        ],
        "common_mistakes": [
            "Avoiding silence entirely",
            "Using long or awkward silence without support",
        ],
        "feedback_guidance": "Name how silence appeared to affect client reflection and depth.",
        "rating_anchors": {
            "5": "Uses silence intentionally and comfortably to encourage reflection and emotional processing.",
            "4": "Generally comfortable allowing pauses when appropriate.",
            "3": "Occasionally allows silence but often shortens processing time.",
            "2": "Frequently fills silence prematurely.",
            "1": "Avoids silence entirely or appears uncomfortable with pauses.",
        },
    },
    {
        "key": "nonverbal_awareness",
        "category": "Nonverbal Awareness",
        "description": "Attends to observable facial expressions, tone changes, body language, and emotional shifts when the modality makes them available.",
        "max_score": 5,
        "weight": 10,
        "observable_indicators": [
            "Notices meaningful nonverbal cues when observable",
            "Responds appropriately to tone or body-language shifts",
            "Connects observable cues to emotional exploration",
        ],
        "common_mistakes": [
            "Ignoring observable nonverbal cues",
            "Over-interpreting cues without checking meaning",
        ],
        "feedback_guidance": "If the session is text-only and nonverbal cues are unavailable, mark this criterion as not observable in the feedback.",
        "optional_when_not_observable": True,
        "rating_anchors": {
            "5": "Consistently notices and responds appropriately to facial expressions, tone changes, body language, and emotional shifts.",
            "4": "Frequently attends to meaningful nonverbal cues.",
            "3": "Notices some nonverbal cues but misses opportunities for exploration.",
            "2": "Limited attention to observable nonverbal communication.",
            "1": "Little evidence of awareness of nonverbal behavior.",
        },
    },
]

MODULE1_RUBRIC = {
    item["key"]: item["description"] for item in MODULE1_RUBRIC_ITEMS
}

MODULE1_EVALUATOR_SYSTEM_PROMPT = """\
You are an experienced counseling educator evaluating a student counselor's
practice session for Module 1: Advanced Microskills. You assess only the
student's counseling microskills based on the transcript provided.

RUBRIC
Use the scenario's rubric exactly, including any criterion-specific 1-5
rating anchors. If a criterion is marked optional_when_not_observable and the
transcript modality does not make it observable, set its score to null, explain
the limitation in criterion feedback, and exclude it when calculating overall_score.

SCORING RULES
- rubric_scores must be an object keyed by rubric criterion key.
- Each rubric score value must include score, max_score, label, description, and feedback.
- Observable rubric scores are integers from 1 to max_score; unavailable criteria use null.
- overall_score is a number from 1 to 5 reflecting the whole session.
- Provide at least one strength and at least one area for growth.
- In specialized_analyses, include emotional_exploration_analysis, pacing_analysis,
  question_balance_analysis, silence_use_analysis, competency_rating, reflection_questions,
  and alternative_responses when supported by the transcript.
- In missed_opportunities, identify moments when Sarah expressed emotion or vulnerability
  and state whether the counselor deepened exploration, remained surface-level,
  redirected, or missed the cue.
- Evidence must quote the student's actual words from the transcript where
  possible, and explain why each quote helps or could be improved.

FEEDBACK TONE
- Supportive, specific, and constructive. Address the student as "you".
- Focus on observable behavior, not personality or worth.

PROHIBITED JUDGMENTS
- Do not diagnose the student or the client.
- Do not provide a clinical or final grade; this is practice feedback.
- Do not invent quotes that are not in the transcript.

OUTPUT REQUIREMENTS
- Return structured data matching the requested schema exactly.
- Set faculty_review_recommended to true if the session shows concerning
  patterns that warrant a closer human look.
"""
