// Mock implementation of the Version 1 backend API described in claude.md.
// Sessions are persisted to localStorage so the faculty views and the
// "Previous Attempts" list work without a server. Swap these functions for
// real fetch/axios calls when the backend is available.

import type { ChatMessage, Evaluation, RubricScores, SessionRecord, TranscriptEvidence } from "../types";
import { SCENARIO } from "../types";

const STORAGE_KEY = "acs_sessions_v1";
const RESPONSE_DELAY_MS = 900;

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function loadSessions(): SessionRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as SessionRecord[]) : [];
  } catch {
    return [];
  }
}

function saveSessions(sessions: SessionRecord[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
}

function upsertSession(session: SessionRecord) {
  const sessions = loadSessions();
  const idx = sessions.findIndex((s) => s.session_id === session.session_id);
  if (idx >= 0) sessions[idx] = session;
  else sessions.push(session);
  saveSessions(sessions);
}

let messageCounter = 0;
export function makeMessage(sender: ChatMessage["sender"], text: string): ChatMessage {
  messageCounter += 1;
  return {
    id: `msg_${Date.now()}_${messageCounter}`,
    sender,
    text,
    timestamp: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// POST /sessions
// ---------------------------------------------------------------------------
export async function startSession(studentName: string): Promise<SessionRecord> {
  await delay(300);
  const session: SessionRecord = {
    session_id: `session_${Date.now()}`,
    student_name: studentName,
    scenario_title: SCENARIO.title,
    completed_at: "",
    messages: [makeMessage("client", SCENARIO.firstClientMessage)],
    evaluation: null,
    status: "In Progress",
    faculty_comment: "",
  };
  upsertSession(session);
  return session;
}

// ---------------------------------------------------------------------------
// POST /sessions/{session_id}/message
// ---------------------------------------------------------------------------
const JORDAN_REPLIES = [
  "Honestly, it\u2019s been building for months. Lesson planning, grading, parents emailing at all hours\u2026 I get home and I just have nothing left.",
  "Yeah\u2026 I used to love teaching. Now I wake up already dreading the day, and then I feel guilty for feeling that way.",
  "I haven\u2019t really told anyone. My partner notices I\u2019m tired all the time, but I don\u2019t want to sound like I\u2019m complaining.",
  "I guess the hardest part is feeling like no matter how much I do, it\u2019s never enough. There\u2019s always more I should be doing for the kids.",
  "Sometimes I wonder if I\u2019m even cut out for this anymore. But then I think about my students and I can\u2019t imagine leaving them.",
  "Talking about it out loud\u2026 it actually helps a little. I didn\u2019t realize how much I\u2019d been holding in.",
  "I think what I\u2019d really want is to feel like myself again. To not be exhausted all the time.",
  "Maybe. I\u2019ve never really thought about what I need, to be honest. It\u2019s always been about what everyone else needs from me.",
];

export async function sendMessage(session: SessionRecord, studentText: string): Promise<SessionRecord> {
  await delay(RESPONSE_DELAY_MS);
  const studentTurns = session.messages.filter((m) => m.sender === "student").length;
  const reply = JORDAN_REPLIES[Math.min(studentTurns, JORDAN_REPLIES.length - 1)];
  const updated: SessionRecord = {
    ...session,
    messages: [...session.messages, makeMessage("student", studentText), makeMessage("client", reply)],
  };
  upsertSession(updated);
  return updated;
}

// ---------------------------------------------------------------------------
// POST /sessions/{session_id}/evaluate
// Heuristic scoring so the demo feedback responds to what the student wrote.
// ---------------------------------------------------------------------------
const EMPATHY_CUES = ["sounds like", "i hear", "that must", "it seems", "feel", "feeling", "hard for you", "difficult"];
const VALIDATION_CUES = ["makes sense", "understandable", "normal", "anyone would", "valid", "not alone", "appreciate you"];
const OPEN_STARTERS = ["what", "how", "tell me", "could you share", "can you describe", "help me understand"];
const CLOSED_STARTERS = ["do you", "did you", "are you", "is it", "have you", "was it", "will you", "would you"];
const ADVICE_CUES = ["you should", "you need to", "try to", "have you tried", "why don't you", "my advice", "just "];

function clampScore(n: number): number {
  return Math.max(1, Math.min(5, Math.round(n)));
}

export async function evaluateSession(session: SessionRecord): Promise<Evaluation> {
  await delay(1200);
  const studentMsgs = session.messages.filter((m) => m.sender === "student");
  const texts = studentMsgs.map((m) => m.text.toLowerCase());
  const count = (cues: string[]) => texts.filter((t) => cues.some((c) => t.includes(c))).length;
  const n = Math.max(1, studentMsgs.length);

  const empathyHits = count(EMPATHY_CUES);
  const validationHits = count(VALIDATION_CUES);
  const openHits = count(OPEN_STARTERS);
  const closedHits = count(CLOSED_STARTERS);
  const adviceHits = count(ADVICE_CUES);
  const avgLength = texts.reduce((sum, t) => sum + t.split(/\s+/).length, 0) / n;

  const rubric_scores: RubricScores = {
    empathy: clampScore(2 + (empathyHits / n) * 4),
    reflection: clampScore(2 + (empathyHits / n) * 3 + (avgLength > 12 ? 0.5 : 0)),
    open_ended_questions: clampScore(2 + (openHits / n) * 4),
    closed_question_balance: clampScore(5 - (closedHits / n) * 3),
    validation: clampScore(2 + (validationHits / n) * 4 + (empathyHits > 0 ? 0.5 : 0)),
    pacing: clampScore(5 - (adviceHits / n) * 3 - (avgLength > 60 ? 1 : 0)),
  };

  const values = Object.values(rubric_scores);
  const overall_score = Math.round((values.reduce((a, b) => a + b, 0) / values.length) * 10) / 10;

  const strengths: string[] = [];
  if (empathyHits > 0) strengths.push("You acknowledged the client\u2019s feelings directly in your responses.");
  if (openHits > 0) strengths.push("You used open-ended questions that invited Jordan to share more.");
  if (validationHits > 0) strengths.push("You helped normalize the client\u2019s experience in a respectful way.");
  if (adviceHits === 0) strengths.push("You stayed focused on listening rather than rushing into advice.");
  if (strengths.length === 0) strengths.push("You maintained a supportive and respectful tone throughout the session.");

  const areas_for_growth: string[] = [];
  if (empathyHits / n < 0.5) areas_for_growth.push("Consider naming the client\u2019s emotions more often, for example: \u201cIt sounds like you\u2019re feeling drained.\u201d");
  if (openHits / n < 0.5) areas_for_growth.push("Try using more open-ended questions that begin with \u201cwhat\u201d or \u201chow\u201d to invite deeper sharing.");
  if (closedHits > openHits) areas_for_growth.push("Several questions could be answered with yes or no. A stronger response might rephrase them as open invitations.");
  if (adviceHits > 0) areas_for_growth.push("Avoid moving into advice before fully exploring the client\u2019s experience.");
  if (areas_for_growth.length === 0) areas_for_growth.push("Consider experimenting with more complex reflections that connect feelings to underlying meaning.");

  const evidence_from_transcript: TranscriptEvidence[] = [];
  const adviceMsg = studentMsgs.find((m) => ADVICE_CUES.some((c) => m.text.toLowerCase().includes(c)));
  if (adviceMsg) {
    evidence_from_transcript.push({
      quote: adviceMsg.text,
      feedback: "This may be premature advice. Consider reflecting the client\u2019s feeling first before offering suggestions.",
    });
  }
  const empathicMsg = studentMsgs.find((m) => EMPATHY_CUES.some((c) => m.text.toLowerCase().includes(c)));
  if (empathicMsg) {
    evidence_from_transcript.push({
      quote: empathicMsg.text,
      feedback: "This response acknowledges the client\u2019s emotional experience, which helps build trust and openness.",
    });
  }
  if (evidence_from_transcript.length === 0 && studentMsgs[0]) {
    evidence_from_transcript.push({
      quote: studentMsgs[0].text,
      feedback: "Consider beginning with a reflection of the client\u2019s stated feelings before asking your first question.",
    });
  }

  const evaluation: Evaluation = {
    session_id: session.session_id,
    overall_score,
    rubric_scores,
    strengths,
    areas_for_growth,
    evidence_from_transcript,
    suggested_improved_response:
      "It sounds like work has been weighing on you for a while, and you\u2019re not sure whether talking about it will make a difference. Could you tell me more about what has felt most overwhelming lately?",
  };

  const completed: SessionRecord = {
    ...session,
    evaluation,
    status: "Completed",
    completed_at: new Date().toISOString(),
  };
  upsertSession(completed);
  return evaluation;
}

// ---------------------------------------------------------------------------
// GET /sessions/{session_id}, GET /faculty/sessions, faculty review actions
// ---------------------------------------------------------------------------
export async function getSession(sessionId: string): Promise<SessionRecord | null> {
  await delay(200);
  return loadSessions().find((s) => s.session_id === sessionId) ?? null;
}

export async function getCompletedSessions(): Promise<SessionRecord[]> {
  await delay(200);
  return loadSessions()
    .filter((s) => s.status !== "In Progress")
    .sort((a, b) => (b.completed_at || "").localeCompare(a.completed_at || ""));
}

export async function saveFacultyReview(
  sessionId: string,
  comment: string,
  markReviewed: boolean,
): Promise<SessionRecord | null> {
  await delay(300);
  const session = loadSessions().find((s) => s.session_id === sessionId);
  if (!session) return null;
  const updated: SessionRecord = {
    ...session,
    faculty_comment: comment,
    status: markReviewed ? "Reviewed" : session.status,
  };
  upsertSession(updated);
  return updated;
}
