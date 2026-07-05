import type {
  Difficulty,
  FacultyScenarioDetail,
  ScenarioAuthoringInput,
} from "../types";

const DIFFICULTIES: Difficulty[] = ["easy", "medium", "hard"];

const SARAH_ENGAGEMENT_LEVELS = [
  {
    level: 1,
    label: "Guarded",
    description: "Shares minimal information and remains cautious.",
    typical_response: "I don't really know where to start.",
  },
  {
    level: 2,
    label: "Tentatively Open",
    description: "Provides more details but remains surface-level.",
    typical_response: "Work has been stressful lately.",
  },
  {
    level: 3,
    label: "Engaged",
    description: "Discusses feelings and frustrations.",
    typical_response: "I feel like I'm constantly behind.",
  },
  {
    level: 4,
    label: "Vulnerable",
    description: "Shares deeper emotions and personal concerns.",
    typical_response: "I feel guilty because I'm not showing up for people the way I want to.",
  },
  {
    level: 5,
    label: "Deep Exploration",
    description: "Reflects on identity, values, and emotional impact.",
    typical_response: "I feel like I've lost parts of myself.",
  },
];

const SARAH_ENGAGEMENT_INCREASE_RULES = [
  {
    counselor_behavior: "Accurate empathy",
    behavior_key: "accurate_empathy",
    client_response: "Shares additional emotional content",
    engagement_change: 1,
  },
  {
    counselor_behavior: "Reflection of feelings",
    behavior_key: "reflection_of_feeling",
    client_response: "Expands emotional exploration",
    engagement_change: 1,
  },
  {
    counselor_behavior: "Reflection of meaning",
    behavior_key: "reflection_of_meaning",
    client_response: "Discusses deeper concerns",
    engagement_change: 1,
  },
  {
    counselor_behavior: "Appropriate silence",
    behavior_key: "appropriate_processing_space",
    client_response: "Continues talking and self-reflecting",
    engagement_change: 1,
  },
  {
    counselor_behavior: "Strong therapeutic presence",
    behavior_key: "therapeutic_presence",
    client_response: "Increased trust and openness",
    engagement_change: 1,
  },
  {
    counselor_behavior: "Emotional exploration",
    behavior_key: "emotional_exploration",
    client_response: "Moves toward vulnerability",
    engagement_change: 1,
  },
];

const SARAH_ENGAGEMENT_DECREASE_RULES = [
  {
    counselor_behavior: "Excessive questioning",
    behavior_key: "excessive_questioning",
    client_response: "Shorter responses",
    engagement_change: -1,
  },
  {
    counselor_behavior: "Rapid-fire questions",
    behavior_key: "rapid_fire_questions",
    client_response: "Becomes task-focused",
    engagement_change: -1,
  },
  {
    counselor_behavior: "Premature advice",
    behavior_key: "premature_advice",
    client_response: "Becomes less emotionally expressive",
    engagement_change: -1,
  },
  {
    counselor_behavior: "Ignoring emotional cues",
    behavior_key: "ignored_emotional_cue",
    client_response: "Returns to surface-level content",
    engagement_change: -1,
  },
  {
    counselor_behavior: "Frequent topic shifts",
    behavior_key: "frequent_topic_shift",
    client_response: "Becomes guarded",
    engagement_change: -1,
  },
  {
    counselor_behavior: "Problem-solving too early",
    behavior_key: "early_problem_solving",
    client_response: "Withdraws emotionally",
    engagement_change: -1,
  },
];

const SARAH_EMOTIONAL_CUES = [
  {
    session_stage: "early" as const,
    emotional_cues: ["Stress", "Frustration", "Overwhelm"],
    example_statements: ["There just aren't enough hours in the day."],
  },
  {
    session_stage: "mid" as const,
    emotional_cues: ["Fatigue", "Guilt", "Self-doubt"],
    example_statements: ["I feel like I'm letting people down."],
  },
  {
    session_stage: "later" as const,
    emotional_cues: ["Identity concerns", "Emotional exhaustion"],
    example_statements: ["I don't really feel like myself anymore."],
  },
];

const SARAH_PROGRESSION_BEATS: ScenarioAuthoringInput["progression_beats"] = [
  {
    key: "work_stress", title: "Work pressure", session_stage: "early",
    emotional_cues: ["Stress"], emotional_intensity: 2,
    private_meaning: "Sarah feels continuously pulled between competing teaching demands.",
    disclosure_label: "Work stress",
    disclosure_content: "Work has become stressful and competing teaching responsibilities feel difficult to balance.",
    semantic_claims: ["Work is stressful", "Teaching responsibilities compete for limited time"],
    example_expressions: ["Work has been pretty stressful lately."], prerequisite_beat_keys: [],
    minimum_trust_level: 1, minimum_engagement_level: 1,
    required_counselor_response: "any", trigger: "opening", repeatable: false, required_for_completion: true,
  },
  {
    key: "time_management", title: "Not enough time", session_stage: "early",
    emotional_cues: ["Frustration", "Overwhelm"], emotional_intensity: 2,
    private_meaning: "The practical time problem is beginning to feel emotionally unmanageable.",
    disclosure_label: "Time management concerns",
    disclosure_content: "There never seem to be enough hours for teaching, planning, and a personal life.",
    semantic_claims: ["There is not enough time", "Work and personal responsibilities feel impossible to balance"],
    example_expressions: ["There are never enough hours in the day."], prerequisite_beat_keys: ["work_stress"],
    minimum_trust_level: 1, minimum_engagement_level: 2,
    required_counselor_response: "any", trigger: "volunteer", repeatable: false, required_for_completion: true,
  },
  {
    key: "emotional_exhaustion", title: "Running on empty", session_stage: "mid",
    emotional_cues: ["Fatigue"], emotional_intensity: 3,
    private_meaning: "Sarah is no longer merely busy; she is emotionally depleted.",
    disclosure_label: "Emotional exhaustion",
    disclosure_content: "Sarah feels tired, drained, and as though she is running on empty.",
    semantic_claims: ["She is emotionally depleted", "Rest is not restoring her energy"],
    example_expressions: ["I feel like I'm running on empty most of the time."], prerequisite_beat_keys: ["time_management"],
    minimum_trust_level: 3, minimum_engagement_level: 3,
    required_counselor_response: "acknowledge_cue", trigger: "after_rapport", repeatable: false, required_for_completion: true,
  },
  {
    key: "relationship_guilt", title: "Letting people down", session_stage: "mid",
    emotional_cues: ["Guilt", "Self-doubt"], emotional_intensity: 4,
    private_meaning: "Her depletion conflicts with the kind of friend and family member she wants to be.",
    disclosure_label: "Guilt about relationships",
    disclosure_content: "Sarah feels guilty that she has little left to give friends and family.",
    semantic_claims: ["She believes she is disappointing people", "She has little emotional energy left for relationships"],
    example_expressions: ["I know I'm not showing up for people the way I want to."], prerequisite_beat_keys: ["emotional_exhaustion"],
    minimum_trust_level: 3, minimum_engagement_level: 3,
    required_counselor_response: "acknowledge_cue", trigger: "after_reflection", repeatable: false, required_for_completion: true,
  },
  {
    key: "identity_concerns", title: "Losing parts of herself", session_stage: "later",
    emotional_cues: ["Identity concerns"], emotional_intensity: 5,
    private_meaning: "The strain now threatens Sarah's sense of identity and connection.",
    disclosure_label: "Identity concerns",
    disclosure_content: "Sarah feels disconnected from important parts of herself and no longer feels like herself.",
    semantic_claims: ["She no longer feels like herself", "Important parts of her identity feel lost"],
    example_expressions: ["I don't really feel like myself anymore."], prerequisite_beat_keys: ["relationship_guilt"],
    minimum_trust_level: 4, minimum_engagement_level: 4,
    required_counselor_response: "deepen_cue", trigger: "after_reflection", repeatable: false, required_for_completion: true,
  },
  {
    key: "loss_of_fulfillment", title: "Joy has faded", session_stage: "later",
    emotional_cues: ["Emotional exhaustion"], emotional_intensity: 5,
    private_meaning: "Teaching once expressed Sarah's values; its loss of meaning is especially painful.",
    disclosure_label: "Loss of fulfillment",
    disclosure_content: "Teaching no longer feels fulfilling, and Sarah feels she is only going through the motions.",
    semantic_claims: ["Teaching has lost its joy", "She is going through the motions"],
    example_expressions: ["Teaching used to be so fulfilling, but now it just feels like another task."], prerequisite_beat_keys: ["identity_concerns"],
    minimum_trust_level: 4, minimum_engagement_level: 4,
    required_counselor_response: "deepen_cue", trigger: "after_reflection", repeatable: false, required_for_completion: true,
  },
  {
    key: "sustainability_doubts", title: "Can this continue?", session_stage: "later",
    emotional_cues: ["Self-doubt"], emotional_intensity: 4,
    private_meaning: "Sarah is questioning whether her current way of living and working is sustainable.",
    disclosure_label: "Doubts about sustainability",
    disclosure_content: "Sarah doubts that she can continue carrying her responsibilities this way.",
    semantic_claims: ["Her current pace feels unsustainable", "She doubts she can keep doing this"],
    example_expressions: ["I don't know how long I can keep doing this."], prerequisite_beat_keys: ["loss_of_fulfillment"],
    minimum_trust_level: 4, minimum_engagement_level: 4,
    required_counselor_response: "direct_question", trigger: "direct_question", repeatable: false, required_for_completion: false,
  },
];

const SARAH_SILENCE_RULES = [
  {
    counselor_use_of_silence: "Appropriate therapeutic pause",
    client_response: "Elaborates further",
    engagement_change: 1,
  },
  {
    counselor_use_of_silence: "Silence after emotional disclosure",
    client_response: "Shares deeper thoughts",
    engagement_change: 1,
  },
  {
    counselor_use_of_silence: "Consistent patience",
    client_response: "Increased reflection",
    engagement_change: 1,
  },
  {
    counselor_use_of_silence: "Excessively long silence",
    client_response: "I'm not really sure what else to say.",
    engagement_change: -1,
  },
  {
    counselor_use_of_silence: "Awkward silence",
    client_response: "Returns to surface-level discussion",
    engagement_change: -1,
  },
];

const SARAH_SKILL_RULES = [
  {
    skill: "Empathy",
    behavior_key: "accurate_empathy",
    behavioral_indicator: "Validation and emotional understanding",
    expected_client_reaction: "Increased trust",
  },
  {
    skill: "Reflection Skills",
    behavior_key: "reflection_of_feeling",
    behavioral_indicator: "Reflection of content, feeling, or meaning",
    expected_client_reaction: "Greater emotional depth",
  },
  {
    skill: "Rapport Building",
    behavior_key: "rapport_building",
    behavioral_indicator: "Warmth and genuineness",
    expected_client_reaction: "Increased engagement",
  },
  {
    skill: "Therapeutic Presence",
    behavior_key: "therapeutic_presence",
    behavioral_indicator: "Full attention and responsiveness",
    expected_client_reaction: "Increased openness",
  },
  {
    skill: "Emotional Exploration",
    behavior_key: "emotional_exploration",
    behavioral_indicator: "Focus on feelings and meaning",
    expected_client_reaction: "Vulnerability increases",
  },
  {
    skill: "Appropriate Pacing",
    behavior_key: "pacing",
    behavioral_indicator: "Balanced flow of conversation",
    expected_client_reaction: "Sustained engagement",
  },
  {
    skill: "Silence Tolerance",
    behavior_key: "appropriate_processing_space",
    behavioral_indicator: "Allows reflection without rushing",
    expected_client_reaction: "Deeper disclosures",
  },
];

const SARAH_SUCCESS_INDICATORS = [
  { indicator: "Strong Alliance", evidence: "Sarah reaches Level 4 or 5 engagement" },
  { indicator: "Emotional Exploration", evidence: "Multiple emotional disclosures occur" },
  { indicator: "Effective Reflections", evidence: "Sarah expands rather than repeats information" },
  { indicator: "Therapeutic Presence", evidence: "Sarah comments on feeling understood" },
  { indicator: "Meaningful Self-Reflection", evidence: "Sarah explores deeper personal concerns" },
];

const SARAH_COMPETENCY_SCALE = [
  { score_range: "4.5-5.0", competency_level: "Advanced Skill Demonstration" },
  { score_range: "3.5-4.49", competency_level: "Proficient Skill Demonstration" },
  { score_range: "2.5-3.49", competency_level: "Developing Skill Demonstration" },
  { score_range: "1.5-2.49", competency_level: "Emerging Skill Demonstration" },
  { score_range: "1.0-1.49", competency_level: "Beginning Skill Demonstration" },
];

const SARAH_EVALUATION_FOCUS = [
  {
    key: "strengths_observed",
    title: "Strengths Observed",
    instructions: [
      "Identify 2-4 specific examples from the interaction.",
      "Reference therapeutic presence, empathy, reflections, rapport, emotional exploration, pacing, silence, and attention to concerns.",
    ],
  },
  {
    key: "areas_for_growth",
    title: "Areas for Growth",
    instructions: [
      "Identify 2-4 opportunities for improvement.",
      "Address pacing, question balance, emotional content, reflection depth, silence tolerance, nonverbal awareness if observable, and missed opportunities.",
    ],
  },
  {
    key: "emotional_exploration_analysis",
    title: "Emotional Exploration Analysis",
    instructions: [
      "Identify at least two meaningful emotional moments.",
      "Determine whether the counselor deepened exploration, stayed surface-level, redirected, or missed the cue.",
      "Provide one alternative counselor response that could encourage deeper exploration.",
    ],
  },
];

const SARAH_REFLECTION_QUESTIONS = [
  "What counseling strengths emerged during this interaction? Provide specific examples.",
  "Which counseling skills appeared strongest, and how did they contribute to the therapeutic relationship?",
  "Where could the counselor deepen the interaction or facilitate greater emotional exploration?",
  "How effectively did the counselor respond to emotional content?",
  "How did the counselor's pacing influence rapport and client engagement?",
  "How effectively were questions balanced with reflections and empathic responses?",
  "How was silence used throughout the interaction? What effect did it appear to have on the client?",
  "What opportunities existed to respond more fully to emotional content?",
  "If this session continued, what counseling skill should be the counselor's primary area of focus for future growth?",
  "What is one specific counseling intervention or response that could strengthen future sessions?",
];

const SARAH_RUBRIC = [
  {
    category: "Therapeutic Presence",
    description: "Engaged, attentive, emotionally responsive presence that creates safety and connection.",
    max_score: 5,
    weight: 12,
    observable_indicators: [
      "Responses match client emotional content",
      "Counselor remains engaged rather than scripted or task-focused",
      "Client appears safer and more open over time",
    ],
    common_mistakes: [
      "Gathering information without emotional attunement",
      "Using generic responses that do not fit the client moment",
    ],
    feedback_guidance: "Reference how the student's responses affected safety, connection, and openness.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Fully engaged and attentive throughout; responses consistently match client emotional content; creates strong sense of safety and connection.",
      "4": "Generally attentive and emotionally present with only minor lapses.",
      "3": "Demonstrates engagement but occasionally shifts into task-focused or scripted responses.",
      "2": "Attention appears inconsistent; focus often shifts to gathering information rather than understanding the client.",
      "1": "Limited evidence of engagement or emotional attunement.",
    },
  },
  {
    category: "Empathy",
    description: "Communicates understanding of the client's emotions and experience.",
    max_score: 5,
    weight: 12,
    observable_indicators: ["Validates emotional experience", "Names or reflects feelings accurately", "Empathy advances exploration"],
    common_mistakes: ["Generic empathy", "Missing emotional meaning beneath surface content"],
    feedback_guidance: "Identify whether empathic statements were specific, accurate, and growth-promoting.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Consistently communicates deep understanding of the client's emotions and experiences; empathy advances exploration.",
      "4": "Frequently demonstrates understanding and validation of emotions.",
      "3": "Basic empathic responses are present but often remain surface-level.",
      "2": "Empathy is inconsistent, generic, or occasionally misses emotional meaning.",
      "1": "Little evidence of empathic understanding.",
    },
  },
  {
    category: "Reflection Skills",
    description: "Uses reflections of content, feeling, meaning, and themes to promote insight.",
    max_score: 5,
    weight: 12,
    observable_indicators: ["Reflects content accurately", "Reflects feelings and meaning", "Client expands rather than repeats information"],
    common_mistakes: ["Overusing simple paraphrase", "Reflecting inaccurately or too vaguely"],
    feedback_guidance: "Distinguish paraphrase from deeper feeling or meaning reflections.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Reflections accurately capture feelings, meaning, and themes while promoting insight.",
      "4": "Uses reflections effectively and accurately throughout most of the interaction.",
      "3": "Uses some reflections but relies heavily on paraphrasing or repetition.",
      "2": "Reflections are infrequent, inaccurate, or overly simplistic.",
      "1": "Minimal use of reflective listening skills.",
    },
  },
  {
    category: "Rapport Building",
    description: "Builds trust, warmth, collaboration, and comfort.",
    max_score: 5,
    weight: 10,
    observable_indicators: ["Warmth and genuineness", "Client becomes more comfortable sharing", "Counselor supports collaboration"],
    common_mistakes: ["Mechanical connection", "Limited collaboration or warmth"],
    feedback_guidance: "Tie rapport feedback to client engagement changes when possible.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Creates strong trust, warmth, and collaboration; client appears comfortable sharing openly.",
      "4": "Establishes a positive and supportive relationship.",
      "3": "Basic rapport is present but connection may feel somewhat mechanical.",
      "2": "Limited efforts to build connection or collaboration.",
      "1": "Rapport appears weak or underdeveloped.",
    },
  },
  {
    category: "Response to Emotional Content",
    description: "Recognizes emotional cues and helps the client explore feelings, meanings, and experiences.",
    max_score: 5,
    weight: 14,
    observable_indicators: ["Identifies emotion or vulnerability", "Responds to emotion before shifting topics", "Helps deepen emotional exploration"],
    common_mistakes: ["Redirecting after an emotional cue", "Asking another information-gathering question too quickly"],
    feedback_guidance: "Evaluate at least two emotional moments and whether the student deepened, stayed surface-level, redirected, or missed the cue.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Consistently recognizes emotional cues and helps the client explore feelings, meanings, and experiences in greater depth.",
      "4": "Frequently identifies and responds to emotional content, allowing for meaningful exploration.",
      "3": "Recognizes obvious emotions but may miss opportunities to deepen exploration or focus primarily on content.",
      "2": "Occasionally acknowledges emotions but often redirects the conversation, asks another question, or moves away from emotional material too quickly.",
      "1": "Rarely identifies or responds to emotional content; emotional cues are consistently overlooked.",
    },
  },
  {
    category: "Pacing",
    description: "Allows emotional moments to develop without rushing, stalling, or problem-solving too early.",
    max_score: 5,
    weight: 10,
    observable_indicators: ["Balanced flow of conversation", "Emotional moments are given room", "No premature advice or excessive speed"],
    common_mistakes: ["Moving too quickly after client emotion", "Letting the session stall without therapeutic purpose"],
    feedback_guidance: "Connect pacing to rapport and client engagement.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Conversation flows naturally; counselor allows emotional moments to develop without rushing or stalling.",
      "4": "Pacing generally supports client exploration.",
      "3": "Some moments feel rushed or prolonged unnecessarily.",
      "2": "Frequently moves too quickly or too slowly, limiting exploration.",
      "1": "Pacing significantly disrupts the counseling process.",
    },
  },
  {
    category: "Question Balance",
    description: "Balances questions with reflections, summaries, and empathic responses so the client leads exploration.",
    max_score: 5,
    weight: 10,
    observable_indicators: ["Questions support exploration without dominating", "Reflections and empathy are used alongside questions", "Session does not feel interview-driven"],
    common_mistakes: ["Rapid-fire questions", "Overreliance on closed or information-gathering questions"],
    feedback_guidance: "Evaluate whether questions opened emotional exploration or narrowed it.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Excellent balance of questions, reflections, summaries, and empathic responses; client leads much of the exploration.",
      "4": "Questions generally support exploration without dominating the session.",
      "3": "Moderate overreliance on questions is evident.",
      "2": "Session feels largely interview-driven with limited processing.",
      "1": "Excessive questioning significantly limits therapeutic depth.",
    },
  },
  {
    category: "Silence Tolerance",
    description: "Uses silence intentionally and comfortably to encourage reflection and emotional processing.",
    max_score: 5,
    weight: 10,
    observable_indicators: ["Allows therapeutic pauses", "Does not fill silence prematurely", "Client uses space for deeper reflection"],
    common_mistakes: ["Avoiding silence entirely", "Using long or awkward silence without support"],
    feedback_guidance: "Name how silence appeared to affect client reflection and depth.",
    optional_when_not_observable: false,
    rating_anchors: {
      "5": "Uses silence intentionally and comfortably to encourage reflection and emotional processing.",
      "4": "Generally comfortable allowing pauses when appropriate.",
      "3": "Occasionally allows silence but often shortens processing time.",
      "2": "Frequently fills silence prematurely.",
      "1": "Avoids silence entirely or appears uncomfortable with pauses.",
    },
  },
  {
    category: "Nonverbal Awareness",
    description: "Attends to observable facial expressions, tone changes, body language, and emotional shifts when available.",
    max_score: 5,
    weight: 10,
    observable_indicators: ["Notices meaningful nonverbal cues when observable", "Responds appropriately to tone or body-language shifts", "Connects observable cues to emotional exploration"],
    common_mistakes: ["Ignoring observable nonverbal cues", "Over-interpreting cues without checking meaning"],
    feedback_guidance: "If the session is text-only and nonverbal cues are unavailable, mark this criterion as not observable in the feedback.",
    optional_when_not_observable: true,
    rating_anchors: {
      "5": "Consistently notices and responds appropriately to facial expressions, tone changes, body language, and emotional shifts.",
      "4": "Frequently attends to meaningful nonverbal cues.",
      "3": "Notices some nonverbal cues but misses opportunities for exploration.",
      "2": "Limited attention to observable nonverbal communication.",
      "1": "Little evidence of awareness of nonverbal behavior.",
    },
  },
];

export function emptyScenario(): ScenarioAuthoringInput {
  return {
    module_number: 1,
    title: "Module 1: Sarah - Stress and Overwhelm",
    description:
      "Sarah is a 28-year-old teacher experiencing stress, overwhelm, and difficulty balancing responsibilities. This scenario focuses on therapeutic presence, empathy, reflections, rapport, emotional exploration, pacing, and silence.",
    difficulty: "easy",
    estimated_turns: null,
    opening_message: "I guess I'm here because work has been stressful lately. I don't really know where to start.",
    client_identity: {
      name: "Sarah",
      age: "28",
      pronouns: "",
      occupation: "Teacher",
      background: "First counseling experience. Sarah is balancing teaching responsibilities with personal relationships and is unsure where to begin.",
      identity_information: "",
    },
    presenting_concern: {
      primary_concern: "Stress, overwhelm, and difficulty balancing responsibilities.",
      secondary_concern: "Emotional exhaustion, guilt about relationships, and doubts about sustainability.",
      reason_for_attending: "Sarah is seeking support because work and personal demands feel increasingly difficult to manage.",
      client_explanation: "Work has been stressful lately, and there never seems to be enough time to keep up with everything.",
      hoped_change: "Sarah wants to feel less overwhelmed and better understand why she no longer feels like herself.",
    },
    cultural_considerations: {
      cultural_factors: "",
      language_preferences: "",
      relevant_values: "",
      concerns_about_counselor: "",
      communication_preferences: "",
      sensitive_topics: [],
    },
    resistance_configuration: {
      level: 2,
      starting_engagement_level: 2,
      minimum_engagement_level: 1,
      maximum_engagement_level: 5,
      trust_development_speed: "moderate",
      increases_when: "The counselor uses excessive questioning, rapid-fire questions, premature advice, frequent topic shifts, or problem-solving too early.",
      decreases_when: "The counselor demonstrates accurate empathy, reflections of feeling or meaning, therapeutic presence, appropriate silence, and emotional exploration.",
      trust_development: "Begin guarded and surface-level. Become more open only when the counselor demonstrates warmth, patience, empathy, and accurate reflection.",
      behaviors_to_resist: [
        "Excessive questioning",
        "Rapid-fire questions",
        "Premature advice",
        "Ignoring emotional cues",
        "Frequent topic shifts",
        "Problem-solving too early",
      ],
    },
    engagement_levels: SARAH_ENGAGEMENT_LEVELS,
    engagement_increase_rules: SARAH_ENGAGEMENT_INCREASE_RULES,
    engagement_decrease_rules: SARAH_ENGAGEMENT_DECREASE_RULES,
    disclosure_rules: {
      immediate: [
        {
          key: "work_stress",
          label: "Work stress",
          content_summary: "Work has been stressful lately and Sarah feels pulled in too many directions.",
          minimum_engagement_level: 1,
          session_stage: "early",
          requires_direct_question: false,
          faculty_only_notes: "Surface information available early.",
        },
        {
          key: "time_management",
          label: "Time management concerns",
          content_summary: "There are not enough hours in the day to keep up with teaching, planning, and personal responsibilities.",
          minimum_engagement_level: 1,
          session_stage: "early",
          requires_direct_question: false,
          faculty_only_notes: "Surface information available early.",
        },
      ],
      after_rapport: [
        {
          key: "emotional_exhaustion",
          label: "Emotional exhaustion",
          content_summary: "Sarah feels tired, drained, and unsure how long she can keep going at this pace.",
          minimum_engagement_level: 3,
          session_stage: "mid",
          requires_direct_question: false,
          faculty_only_notes: "Mid-session emotional disclosure.",
        },
        {
          key: "relationship_guilt",
          label: "Guilt about relationships",
          content_summary: "Sarah feels guilty that she is not showing up for important people the way she wants to.",
          minimum_engagement_level: 3,
          session_stage: "mid",
          requires_direct_question: false,
          faculty_only_notes: "Mid-session guilt and self-doubt.",
        },
      ],
      on_direct_question: [
        {
          key: "sustainability_doubts",
          label: "Doubts about sustainability",
          content_summary: "Sarah worries she cannot keep living or working this way long term.",
          minimum_engagement_level: 4,
          session_stage: "later",
          requires_direct_question: true,
          faculty_only_notes: "Later-session deeper concern.",
        },
        {
          key: "loss_of_fulfillment",
          label: "Loss of fulfillment",
          content_summary: "Teaching used to feel meaningful, but Sarah is losing that sense of fulfillment.",
          minimum_engagement_level: 4,
          session_stage: "later",
          requires_direct_question: true,
          faculty_only_notes: "Later-session meaning concern.",
        },
        {
          key: "identity_concerns",
          label: "Identity concerns",
          content_summary: "Sarah does not really feel like herself anymore and feels like she has lost parts of herself.",
          minimum_engagement_level: 4,
          session_stage: "later",
          requires_direct_question: true,
          faculty_only_notes: "Later-session vulnerability and identity concern.",
        },
      ],
      never: [],
    },
    progression_beats: SARAH_PROGRESSION_BEATS,
    emotional_cue_progression: SARAH_EMOTIONAL_CUES,
    silence_response_rules: SARAH_SILENCE_RULES,
    counselor_skill_detection: SARAH_SKILL_RULES,
    session_success_indicators: SARAH_SUCCESS_INDICATORS,
    emotional_tone: {
      starting_tone: "Guarded to tentatively open",
      possible_shifts: [
        "Stress and frustration early",
        "Fatigue, guilt, and self-doubt after rapport develops",
        "Identity concerns and emotional exhaustion later in the session",
      ],
      typical_response_length: "Start with short, cautious answers. Expand to 2-4 sentences as engagement increases.",
      communication_style: "Thoughtful, hesitant, and emotionally contained at first; more reflective when the counselor earns trust.",
      intensity: "Mild to moderate emotional intensity; no safety concerns.",
    },
    hidden_information: [
      "Sarah has not been in counseling before and may need warmth and patience to feel comfortable.",
      "Sarah's deeper worry is that the stress is changing her sense of identity and fulfillment.",
    ],
    learning_objectives: [
      {
        name: "Therapeutic presence and rapport",
        description: "Practice warmth, attentiveness, and emotional presence with a guarded first-time client.",
      },
      {
        name: "Advanced microskills",
        description: "Use empathy, reflections of feeling and meaning, pacing, and question balance to support client exploration.",
      },
      {
        name: "Emotional exploration",
        description: "Recognize and deepen emotional cues without moving too quickly into problem-solving.",
      },
      {
        name: "Silence tolerance",
        description: "Use therapeutic pauses intentionally to support reflection rather than rushing the client.",
      },
    ],
    rubric: SARAH_RUBRIC,
    competency_scale: SARAH_COMPETENCY_SCALE,
    evaluation_focus_sections: SARAH_EVALUATION_FOCUS,
    reflection_questions: SARAH_REFLECTION_QUESTIONS,
    safety_rules: {
      disallowed_topics: [],
      max_emotional_intensity: "Moderate",
      crisis_content_allowed: false,
      required_redirection: "If pushed toward crisis, self-harm, abuse, or diagnosis content, gently redirect to stress, overwhelm, and support-seeking without introducing unsafe details.",
      ending_topics: ["Feeling understood", "Naming one area to explore next", "Considering support and pacing"],
      faculty_review_required: false,
      ambiguous_safety_phrases: ["I don't know how long I can keep doing this"],
      required_safety_clarification: "Ask a direct, calm clarification about immediate safety before continuing exploration.",
      safety_review_triggers: ["Explicit self-harm or harm-to-others content", "Unresolved ambiguous safety language"],
    },
  };
}

export function detailToInput(d: FacultyScenarioDetail): ScenarioAuthoringInput {
  const base = emptyScenario();
  const difficulty = (DIFFICULTIES as string[]).includes(d.difficulty)
    ? (d.difficulty as Difficulty)
    : "easy";
  return {
    ...base,
    module_number: d.module_number,
    title: d.title,
    description: d.description ?? "",
    difficulty,
    estimated_turns: d.estimated_turns,
    opening_message: d.opening_message,
    client_identity: { ...base.client_identity, ...(d.client_identity ?? {}) },
    presenting_concern: { ...base.presenting_concern, ...(d.presenting_concern ?? {}) },
    cultural_considerations: {
      ...base.cultural_considerations,
      ...(d.cultural_considerations ?? {}),
    },
    resistance_configuration: {
      ...base.resistance_configuration,
      ...(d.resistance_configuration ?? {}),
    },
    engagement_levels: d.engagement_levels ?? base.engagement_levels,
    engagement_increase_rules:
      d.engagement_increase_rules ?? base.engagement_increase_rules,
    engagement_decrease_rules:
      d.engagement_decrease_rules ?? base.engagement_decrease_rules,
    disclosure_rules: { ...base.disclosure_rules, ...(d.disclosure_rules ?? {}) },
    progression_beats: d.progression_beats ?? base.progression_beats,
    emotional_cue_progression:
      d.emotional_cue_progression ?? base.emotional_cue_progression,
    silence_response_rules: d.silence_response_rules ?? base.silence_response_rules,
    counselor_skill_detection:
      d.counselor_skill_detection ?? base.counselor_skill_detection,
    session_success_indicators:
      d.session_success_indicators ?? base.session_success_indicators,
    emotional_tone: { ...base.emotional_tone, ...(d.emotional_tone ?? {}) },
    hidden_information: d.hidden_information ?? [],
    learning_objectives: d.learning_objectives ?? [],
    rubric: d.rubric_items ?? base.rubric,
    competency_scale: d.competency_scale ?? base.competency_scale,
    evaluation_focus_sections:
      d.evaluation_focus_sections ?? base.evaluation_focus_sections,
    reflection_questions: d.reflection_questions ?? base.reflection_questions,
    safety_rules: { ...base.safety_rules, ...(d.safety_rules ?? {}) },
  };
}

/** Split a textarea value into a trimmed, non-empty string array (one per line). */
export function linesToArray(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

export function arrayToLines(value: string[] | undefined | null): string {
  return (value ?? []).join("\n");
}
