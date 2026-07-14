// Frontend types mirror the backend API contracts (see backend/app/schemas).

export type Role = "student" | "faculty";

export type Speaker = "client" | "student" | "system";

export type Modality = "text" | "audio" | "video";

export const MODALITY_LABELS: Record<Modality, string> = {
  text: "Text chat",
  audio: "Voice call",
  video: "Video call",
};

export type SessionStatus =
  | "active"
  | "completed"
  | "evaluating"
  | "evaluated"
  | "failed"
  | "reviewed";

export type ReviewStatus = "pending" | "reviewed" | "needs_revision";

export interface ChatMessage {
  id: string;
  speaker: Speaker;
  content: string;
  sequence_number: number;
  created_at: string;
}

export interface RubricCriterionScore {
  score: number | null;
  max_score: number;
  label?: string | null;
  description?: string | null;
  feedback?: string | null;
}

export type RubricScoreValue = number | RubricCriterionScore;
export type RubricScores = Record<string, RubricScoreValue>;

export interface TranscriptEvidence {
  quote: string;
  feedback: string;
}

export interface Evaluation {
  id: string;
  session_id: string;
  scenario_version_id?: string | null;
  template_key?: string | null;
  template_version?: string | null;
  rubric_version?: string | null;
  output_schema_version?: string | null;
  overall_score: number;
  rubric_scores: RubricScores;
  strengths: string[];
  areas_for_growth: string[];
  evidence_from_transcript: TranscriptEvidence[];
  suggested_improved_response: string;
  specialized_analyses?: Record<string, unknown> | null;
  missed_opportunities?: Record<string, unknown>[] | null;
  faculty_review_recommended?: boolean;
  created_at: string;
  disclaimer: string;
}

export interface SessionDetail {
  id: string;
  student_id: string;
  scenario_id: string;
  scenario_version_id?: string | null;
  status: SessionStatus;
  modality?: Modality;
  student_message_count: number;
  started_at: string | null;
  ended_at: string | null;
  created_at: string;
  scenario_title: string;
  client_name: string;
  student_name: string;
  messages: ChatMessage[];
  evaluation: Evaluation | null;
}

export interface SendMessageResult {
  session_id: string;
  message: ChatMessage;
}

export interface SendAudioMessageResult {
  session_id: string;
  /** What the student's spoken turn was transcribed to. */
  transcript: string;
  /** The client's text reply. */
  message: ChatMessage;
  /** The client reply synthesized to speech (base64-encoded WAV). */
  audio_base64: string;
  audio_mime_type: string;
}

export interface StudentSessionSummary {
  session_id: string;
  scenario_title: string;
  status: SessionStatus;
  overall_score: number | null;
  created_at: string;
  completed_at: string | null;
}

export interface FacultySessionSummary {
  session_id: string;
  student_name: string;
  scenario_title: string;
  status: SessionStatus;
  overall_score: number | null;
  completed_at: string | null;
  review_status: ReviewStatus | null;
}

export interface FacultySessionDetail extends SessionDetail {
  faculty_comment: string;
  review_status: ReviewStatus | null;
  adjusted_score: number | null;
  prompt_trace?: PromptTrace | null;
}

export interface ScenarioSummary {
  id: string;
  module_number: number;
  template_key: string;
  template_version: string;
  current_version_id: string | null;
  title: string;
  slug: string;
  difficulty: string;
  client_name: string;
  is_active: boolean;
}

export interface ScenarioDetail {
  id: string;
  module_number: number;
  template_key: string;
  template_version: string;
  current_version_id: string | null;
  title: string;
  slug: string;
  description: string;
  difficulty: string;
  client_name: string;
  client_profile: Record<string, unknown>;
  student_goal: string;
  rubric_json: Record<string, string>;
  is_active: boolean;
}

export interface FacultyReviewPayload {
  comments: string;
  adjusted_score: number | null;
  review_status: ReviewStatus;
}

export const RUBRIC_LABELS: Record<string, { label: string; meaning: string }> = {
  empathy: { label: "Empathy", meaning: "Ability to acknowledge client feelings" },
  reflection: { label: "Reflection", meaning: "Ability to reflect meaning or emotion" },
  open_ended_questions: { label: "Open-ended Questions", meaning: "Ability to invite deeper sharing" },
  closed_question_balance: { label: "Closed Question Balance", meaning: "Avoiding overuse of yes/no questions" },
  validation: { label: "Validation", meaning: "Ability to respect and normalize client experience" },
  pacing: { label: "Pacing", meaning: "Avoiding rushing, overloading, or premature advice" },
};

// Human-readable labels for backend session statuses.
export const STATUS_LABELS: Record<SessionStatus, string> = {
  active: "In Progress",
  completed: "Completed",
  evaluating: "Evaluating",
  evaluated: "Evaluated",
  failed: "Failed",
  reviewed: "Reviewed",
};

// Minimum student messages required before a session can be evaluated.
// Mirrors the backend MIN_STUDENT_MESSAGES setting.
export const MIN_STUDENT_MESSAGES = 4;

// --- Faculty scenario authoring -------------------------------------------

export type ScenarioStatus = "draft" | "ready_for_testing" | "published" | "inactive";
export type Difficulty = "easy" | "medium" | "hard";

export interface ClientIdentity {
  name: string;
  age?: string | null;
  pronouns?: string | null;
  occupation?: string | null;
  background?: string | null;
  identity_information?: string | null;
}

export interface PresentingConcern {
  primary_concern: string;
  secondary_concern?: string | null;
  reason_for_attending?: string | null;
  client_explanation?: string | null;
  hoped_change?: string | null;
}

export interface CulturalConsiderations {
  cultural_factors?: string | null;
  language_preferences?: string | null;
  relevant_values?: string | null;
  concerns_about_counselor?: string | null;
  communication_preferences?: string | null;
  sensitive_topics: string[];
}

export interface ResistanceConfiguration {
  level: number;
  starting_engagement_level: number;
  minimum_engagement_level: number;
  maximum_engagement_level: number;
  trust_development_speed: "slow" | "moderate" | "fast";
  increases_when?: string | null;
  decreases_when?: string | null;
  trust_development?: string | null;
  behaviors_to_resist: string[];
}

export interface EngagementLevelDescription {
  level: number;
  label: string;
  description: string;
  typical_response?: string | null;
}

export interface ClientBehaviorRule {
  counselor_behavior: string;
  behavior_key?: string | null;
  client_response: string;
  engagement_change: number;
}

export interface EmotionalCueRule {
  session_stage: "early" | "mid" | "later";
  emotional_cues: string[];
  example_statements: string[];
}

export interface SilenceResponseRule {
  counselor_use_of_silence: string;
  client_response: string;
  engagement_change: number;
}

export interface CounselorSkillRule {
  skill: string;
  behavior_key?: string | null;
  behavioral_indicator: string;
  expected_client_reaction: string;
}

export interface SessionSuccessIndicator {
  indicator: string;
  evidence: string;
}

export interface DisclosureItem {
  key?: string | null;
  label: string;
  content_summary: string;
  minimum_engagement_level: number;
  session_stage: "early" | "mid" | "later";
  requires_direct_question: boolean;
  faculty_only_notes?: string | null;
}

export interface DisclosureRules {
  immediate: DisclosureItem[];
  after_rapport: DisclosureItem[];
  on_direct_question: DisclosureItem[];
  never: string[];
}

export interface ProgressionBeat {
  key: string;
  title: string;
  session_stage: "early" | "mid" | "later";
  emotional_cues: string[];
  emotional_intensity: number;
  private_meaning?: string | null;
  disclosure_label?: string | null;
  disclosure_content?: string | null;
  semantic_claims: string[];
  example_expressions: string[];
  prerequisite_beat_keys: string[];
  minimum_trust_level: number;
  minimum_engagement_level: number;
  required_counselor_response: "any" | "acknowledge_cue" | "deepen_cue" | "direct_question" | "therapeutic_pause";
  trigger: "opening" | "volunteer" | "after_rapport" | "direct_question" | "after_reflection" | "after_pause";
  repeatable: boolean;
  required_for_completion: boolean;
  faculty_only_notes?: string | null;
}

export interface EmotionalTone {
  starting_tone?: string | null;
  possible_shifts: string[];
  typical_response_length?: string | null;
  communication_style?: string | null;
  intensity?: string | null;
}

export interface LearningObjective {
  name: string;
  description?: string | null;
}

export interface RubricItem {
  category: string;
  description?: string | null;
  max_score: number;
  weight: number;
  observable_indicators: string[];
  common_mistakes: string[];
  feedback_guidance?: string | null;
  rating_anchors: Record<string, string>;
  optional_when_not_observable: boolean;
}

export interface CompetencyScaleBand {
  score_range: string;
  competency_level: string;
}

export interface EvaluationFocusSection {
  key: string;
  title: string;
  instructions: string[];
}

export interface SafetyRules {
  disallowed_topics: string[];
  max_emotional_intensity?: string | null;
  crisis_content_allowed: boolean;
  required_redirection?: string | null;
  ending_topics: string[];
  faculty_review_required: boolean;
  ambiguous_safety_phrases: string[];
  required_safety_clarification?: string | null;
  safety_review_triggers: string[];
}

export interface ScenarioAuthoringInput {
  module_number: number;
  title: string;
  description?: string | null;
  difficulty: Difficulty;
  estimated_turns?: number | null;
  opening_message?: string | null;
  client_identity: ClientIdentity;
  presenting_concern: PresentingConcern;
  cultural_considerations: CulturalConsiderations;
  resistance_configuration: ResistanceConfiguration;
  engagement_levels: EngagementLevelDescription[];
  engagement_increase_rules: ClientBehaviorRule[];
  engagement_decrease_rules: ClientBehaviorRule[];
  disclosure_rules: DisclosureRules;
  progression_beats: ProgressionBeat[];
  emotional_cue_progression: EmotionalCueRule[];
  silence_response_rules: SilenceResponseRule[];
  counselor_skill_detection: CounselorSkillRule[];
  session_success_indicators: SessionSuccessIndicator[];
  emotional_tone: EmotionalTone;
  hidden_information: string[];
  learning_objectives: LearningObjective[];
  rubric: RubricItem[];
  competency_scale: CompetencyScaleBand[];
  evaluation_focus_sections: EvaluationFocusSection[];
  reflection_questions: string[];
  safety_rules: SafetyRules;
}

export interface ScenarioTemplate {
  key: string;
  version: string;
  display_name: string;
  supported_modalities: string[];
  output_schema_version: string;
  default_rubric: Record<string, unknown>[];
  default_safety_policy: Record<string, unknown>;
  content: Record<string, unknown>;
}

export interface FacultyScenarioSummary {
  id: string;
  module_number: number;
  template_key: string;
  template_version: string;
  current_version_id: string | null;
  title: string;
  slug: string;
  difficulty: string;
  status: ScenarioStatus;
  client_name: string;
  prompt_version: string | null;
  created_by: string | null;
  updated_at: string;
}

export interface FacultyScenarioDetail {
  id: string;
  module_number: number;
  template_key: string;
  template_version: string;
  current_version_id: string | null;
  title: string;
  slug: string;
  description: string;
  difficulty: string;
  estimated_turns: number | null;
  opening_message: string | null;
  status: ScenarioStatus;
  client_identity: ClientIdentity | null;
  presenting_concern: PresentingConcern | null;
  cultural_considerations: CulturalConsiderations | null;
  resistance_configuration: ResistanceConfiguration | null;
  engagement_levels: EngagementLevelDescription[] | null;
  engagement_increase_rules: ClientBehaviorRule[] | null;
  engagement_decrease_rules: ClientBehaviorRule[] | null;
  disclosure_rules: DisclosureRules | null;
  progression_beats: ProgressionBeat[] | null;
  emotional_cue_progression: EmotionalCueRule[] | null;
  silence_response_rules: SilenceResponseRule[] | null;
  counselor_skill_detection: CounselorSkillRule[] | null;
  session_success_indicators: SessionSuccessIndicator[] | null;
  emotional_tone: EmotionalTone | null;
  hidden_information: string[] | null;
  learning_objectives: LearningObjective[] | null;
  rubric_items: RubricItem[] | null;
  competency_scale: CompetencyScaleBand[] | null;
  evaluation_focus_sections: EvaluationFocusSection[] | null;
  reflection_questions: string[] | null;
  safety_rules: SafetyRules | null;
  generated_prompt: string | null;
  prompt_version: string | null;
  prompt_generated_at: string | null;
  created_by: string | null;
  published_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScenarioPreviewResponse {
  status: ScenarioStatus;
  prompt_text: string;
  evaluator_prompt_text: string;
  prompt_version: string;
  warnings: string[];
}

export interface ScenarioPublishResponse {
  id: string;
  status: ScenarioStatus;
  slug: string;
  prompt_version: string | null;
  scenario_version_id: string | null;
  template_key: string;
  template_version: string;
}

export interface TestTurn {
  speaker: "client" | "student";
  content: string;
}

export interface ClientResponsePlanTrace {
  turn: number;
  session_stage: string;
  client_stance: string;
  engagement_level: number;
  trust_level: number;
  emotional_depth: number;
  rupture_count: number;
  counselor_effect: string;
  previous_cue_response?: string | null;
  active_emotional_cues: string[];
  permitted_emotional_cues: string[];
  selected_disclosure_key?: string | null;
  selected_progression_beat_key?: string | null;
  selected_disclosure_label?: string | null;
  selected_disclosure_content?: string | null;
  eligible_disclosure_keys: string[];
  blocked_disclosure_keys: string[];
  already_revealed_keys: string[];
  maximum_new_disclosures: number;
}

export interface ClientResponseValidationTrace {
  accepted: boolean;
  detected_disclosure_keys: string[];
  detected_emotional_cues: string[];
  unauthorized_emotional_cues: string[];
  unauthorized_disclosure_keys: string[];
  ambiguous_disclosure_keys: string[];
  violations: string[];
  validator: string;
  disclosure_findings?: Array<{
    disclosure_key: string;
    status: string;
    confidence: number;
    evidence: string;
    reason: string;
  }>;
  cue_findings?: Array<{
    cue: string;
    status: string;
    confidence: number;
    evidence: string;
    reason: string;
  }>;
  safety_finding?: {
    status: "none" | "ambiguous" | "explicit";
    category?: string | null;
    confidence: number;
    evidence: string;
    reason: string;
  };
  requires_safety_clarification?: boolean;
}

export interface PromptTrace {
    base_client_prompt_text: string;
    latest_runtime_context_text: string;
    latest_client_stateful_system_prompt_text: string;
    latest_client_conversation_prompt_text: string;
    evaluation_transcript_text?: string;
    evaluator_system_prompt_text?: string;
    evaluator_user_prompt_text?: string;
    final_evaluation_prompt_text?: string;
    state_history: Record<string, unknown>[];
    simulation_fidelity?: Record<string, unknown>;
    turn_traces: Array<{
      student_turn_count: number;
      student_message: string;
      detected_behaviors: string[];
      counselor_analysis?: Record<string, unknown> | null;
      cue_response_analysis?: {
        cue?: string | null;
        cue_key?: string | null;
        status: string;
        confidence: number;
        client_evidence: string;
        counselor_evidence: string;
        rationale: string;
        analyzer: string;
      } | null;
      expected_client_reactions?: string[];
      engagement_delta: number;
      trust_delta?: number;
      engagement_level: number;
      trust_level: number;
      emotional_depth?: number;
      rupture_count?: number;
      repair_count?: number;
      disclosure_stage: number;
      session_stage: string;
      stage_gate?: {
        target_stage: string;
        satisfied: boolean;
        time_and_trust_ready?: boolean;
        milestone_ready?: boolean;
        progression_basis?: string;
        required_trust_level?: number;
        required_engagement_level?: number;
        required_beat_keys: string[];
        missing_beat_keys: string[];
        unresolved_beat_keys?: string[];
        blocking_cues: Array<Record<string, unknown>>;
        legacy_compatible: boolean;
      } | null;
      allowed_disclosures: string[];
      response_plan?: ClientResponsePlanTrace | null;
      validation?: ClientResponseValidationTrace | null;
      generation_attempts?: Array<Record<string, unknown>>;
      revealed_information?: string[];
      emotional_cues?: unknown[];
      beat_states?: unknown[];
      runtime_context_text: string;
      client_stateful_system_prompt_text: string;
      client_conversation_prompt_text: string;
    }>;
}

export interface ScenarioTestMessageResponse {
  reply: string;
  debug_state?: {
    template_key: string;
    template_version: string;
    engagement_level: number;
    trust_level: number;
    disclosure_stage: number;
    session_stage: string;
    detected_behaviors: string[];
    expected_client_reactions?: string[];
    allowed_disclosures: string[];
    selected_disclosure_key?: string | null;
    revealed_information?: string[];
    emotional_cues?: unknown[];
    beat_states?: unknown[];
  } | null;
  trace?: PromptTrace | null;
}

export const SCENARIO_STATUS_LABELS: Record<ScenarioStatus, string> = {
  draft: "Draft",
  ready_for_testing: "Ready for testing",
  published: "Published",
  inactive: "Inactive",
};
