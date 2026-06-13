export type Role = "student" | "faculty";

export interface ChatMessage {
  id: string;
  sender: "client" | "student";
  text: string;
  timestamp: string;
}

export interface RubricScores {
  empathy: number;
  reflection: number;
  open_ended_questions: number;
  closed_question_balance: number;
  validation: number;
  pacing: number;
}

export interface TranscriptEvidence {
  quote: string;
  feedback: string;
}

export interface Evaluation {
  session_id: string;
  overall_score: number;
  rubric_scores: RubricScores;
  strengths: string[];
  areas_for_growth: string[];
  evidence_from_transcript: TranscriptEvidence[];
  suggested_improved_response: string;
}

export interface SessionRecord {
  session_id: string;
  student_name: string;
  scenario_title: string;
  completed_at: string;
  messages: ChatMessage[];
  evaluation: Evaluation | null;
  status: "In Progress" | "Completed" | "Reviewed";
  faculty_comment: string;
}

export const RUBRIC_LABELS: Record<keyof RubricScores, { label: string; meaning: string }> = {
  empathy: { label: "Empathy", meaning: "Ability to acknowledge client feelings" },
  reflection: { label: "Reflection", meaning: "Ability to reflect meaning or emotion" },
  open_ended_questions: { label: "Open-ended Questions", meaning: "Ability to invite deeper sharing" },
  closed_question_balance: { label: "Closed Question Balance", meaning: "Avoiding overuse of yes/no questions" },
  validation: { label: "Validation", meaning: "Ability to respect and normalize client experience" },
  pacing: { label: "Pacing", meaning: "Avoiding rushing, overloading, or premature advice" },
};

export const SCENARIO = {
  id: "module1_overwhelmed_teacher",
  title: "Module 1: Overwhelmed Teacher",
  clientName: "Jordan",
  difficulty: "Easy",
  skills: ["Empathy", "Reflection", "Open-ended questions", "Validation", "Pacing"],
  description:
    "You will speak with Jordan, a 29-year-old middle school teacher who feels overwhelmed and emotionally drained at work. Jordan is cooperative but hesitant and may only open up if you use empathy, reflection, and open-ended questions.",
  goal:
    "Demonstrate basic counseling microskills, including empathy, reflection, open-ended questioning, validation, and appropriate pacing.",
  disclaimer:
    "This is a practice simulation. AI-generated feedback is for learning support and should not be treated as a final clinical evaluation.",
  reminder:
    "Try to respond like a beginning counselor. Avoid giving advice too quickly. Focus on listening, reflecting, and inviting the client to share more.",
  firstClientMessage:
    "I guess I\u2019m here because I\u2019ve just been feeling really overwhelmed with work. I don\u2019t know if talking about it will actually help, though.",
};
