// Real backend client for the AI-Assisted Counseling Simulator API.
// The base URL can be overridden via VITE_API_BASE_URL (see .env.example).

import type {
  Evaluation,
  FacultyReviewPayload,
  FacultyScenarioDetail,
  FacultyScenarioSummary,
  FacultySessionDetail,
  FacultySessionSummary,
  ScenarioAuthoringInput,
  ScenarioDetail,
  ScenarioPreviewResponse,
  ScenarioPublishResponse,
  ScenarioSummary,
  ScenarioTemplate,
  NonverbalSummary,
  ScenarioTestMessageResponse,
  SendAudioMessageResult,
  SendMessageResult,
  SessionDetail,
  StudentSessionSummary,
  TestTurn,
} from "../types";
import type { Modality } from "../types";

const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  /** When true, sends the demo faculty role header for faculty endpoints. */
  asFaculty?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.asFaculty) headers["X-Demo-Role"] = "faculty";

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: options.method ?? "GET",
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Unable to reach the simulator service. Is the backend running?");
  }

  if (!response.ok) {
    const message = await extractError(response);
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

async function extractError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail[0]?.msg) return data.detail[0].msg;
  } catch {
    // fall through to default message
  }
  return `Request failed (${response.status}).`;
}

// --- Scenarios -------------------------------------------------------------
export function listScenarios(): Promise<ScenarioSummary[]> {
  return request<ScenarioSummary[]>("/scenarios");
}

export function getScenario(scenarioId: string): Promise<ScenarioDetail> {
  return request<ScenarioDetail>(`/scenarios/${scenarioId}`);
}

/** Convenience: load the first active scenario's full detail. */
export async function getActiveScenario(): Promise<ScenarioDetail> {
  const scenarios = await listScenarios();
  if (scenarios.length === 0) {
    throw new ApiError(404, "No active scenarios are available.");
  }
  return getScenario(scenarios[0].id);
}

// --- Sessions --------------------------------------------------------------
export function startSession(
  scenarioId: string,
  modality: Modality = "text",
): Promise<SessionDetail> {
  return request<SessionDetail>("/sessions", {
    method: "POST",
    body: { scenario_id: scenarioId, modality },
  });
}

export function listMySessions(): Promise<StudentSessionSummary[]> {
  return request<StudentSessionSummary[]>("/sessions");
}

export function getSession(sessionId: string): Promise<SessionDetail> {
  return request<SessionDetail>(`/sessions/${sessionId}`);
}

export function sendMessage(sessionId: string, content: string): Promise<SendMessageResult> {
  return request<SendMessageResult>(`/sessions/${sessionId}/messages`, {
    method: "POST",
    body: { content },
  });
}

/**
 * Upload a recorded student audio turn. The backend transcribes it, runs the
 * same text pipeline, and returns the client's text + synthesized speech.
 * Uses multipart/form-data, so it bypasses the JSON `request` helper.
 */
export async function sendAudioMessage(
  sessionId: string,
  audio: Blob,
): Promise<SendAudioMessageResult> {
  const form = new FormData();
  const extension = audio.type.includes("mp4") ? "mp4" : "webm";
  form.append("audio", audio, `turn.${extension}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/audio-messages`, {
      method: "POST",
      body: form,
    });
  } catch {
    throw new ApiError(0, "Unable to reach the simulator service. Is the backend running?");
  }
  if (!response.ok) {
    throw new ApiError(response.status, await extractError(response));
  }
  return (await response.json()) as SendAudioMessageResult;
}

export function completeSession(
  sessionId: string,
  nonverbalSummary?: NonverbalSummary,
): Promise<SessionDetail> {
  return request<SessionDetail>(`/sessions/${sessionId}/complete`, {
    method: "POST",
    body: nonverbalSummary ? { nonverbal_summary: nonverbalSummary } : undefined,
  });
}

// --- Evaluations -----------------------------------------------------------
export function evaluateSession(sessionId: string): Promise<Evaluation> {
  return request<Evaluation>(`/sessions/${sessionId}/evaluation`, { method: "POST" });
}

export function getEvaluation(sessionId: string): Promise<Evaluation> {
  return request<Evaluation>(`/sessions/${sessionId}/evaluation`);
}

// --- Faculty ---------------------------------------------------------------
export function listFacultySessions(): Promise<FacultySessionSummary[]> {
  return request<FacultySessionSummary[]>("/faculty/sessions", { asFaculty: true });
}

export function getFacultySession(sessionId: string): Promise<FacultySessionDetail> {
  return request<FacultySessionDetail>(`/faculty/sessions/${sessionId}`, { asFaculty: true });
}

export function saveFacultyReview(
  sessionId: string,
  payload: FacultyReviewPayload,
): Promise<unknown> {
  return request(`/faculty/sessions/${sessionId}/review`, {
    method: "POST",
    body: payload,
    asFaculty: true,
  });
}

// --- Faculty scenario authoring -------------------------------------------
export function listScenarioTemplates(): Promise<ScenarioTemplate[]> {
  return request<ScenarioTemplate[]>("/faculty/scenario-templates", { asFaculty: true });
}

export function listFacultyScenarios(): Promise<FacultyScenarioSummary[]> {
  return request<FacultyScenarioSummary[]>("/faculty/scenarios", { asFaculty: true });
}

export function getFacultyScenario(scenarioId: string): Promise<FacultyScenarioDetail> {
  return request<FacultyScenarioDetail>(`/faculty/scenarios/${scenarioId}`, {
    asFaculty: true,
  });
}

export function createScenario(
  payload: ScenarioAuthoringInput,
): Promise<FacultyScenarioDetail> {
  return request<FacultyScenarioDetail>("/faculty/scenarios", {
    method: "POST",
    body: payload,
    asFaculty: true,
  });
}

export function updateScenario(
  scenarioId: string,
  payload: ScenarioAuthoringInput,
): Promise<FacultyScenarioDetail> {
  return request<FacultyScenarioDetail>(`/faculty/scenarios/${scenarioId}`, {
    method: "PATCH",
    body: payload,
    asFaculty: true,
  });
}

export function generateScenarioPreview(
  scenarioId: string,
): Promise<ScenarioPreviewResponse> {
  return request<ScenarioPreviewResponse>(
    `/faculty/scenarios/${scenarioId}/generate-preview`,
    { method: "POST", asFaculty: true },
  );
}

export function testScenarioMessage(
  scenarioId: string,
  content: string,
  history: TestTurn[],
): Promise<ScenarioTestMessageResponse> {
  return request<ScenarioTestMessageResponse>(
    `/faculty/scenarios/${scenarioId}/test-message`,
    { method: "POST", body: { content, history }, asFaculty: true },
  );
}

export function publishScenario(scenarioId: string): Promise<ScenarioPublishResponse> {
  return request<ScenarioPublishResponse>(`/faculty/scenarios/${scenarioId}/publish`, {
    method: "POST",
    asFaculty: true,
  });
}

export function duplicateScenario(scenarioId: string): Promise<FacultyScenarioDetail> {
  return request<FacultyScenarioDetail>(`/faculty/scenarios/${scenarioId}/duplicate`, {
    method: "POST",
    asFaculty: true,
  });
}

export function deactivateScenario(scenarioId: string): Promise<FacultyScenarioDetail> {
  return request<FacultyScenarioDetail>(`/faculty/scenarios/${scenarioId}/deactivate`, {
    method: "POST",
    asFaculty: true,
  });
}
