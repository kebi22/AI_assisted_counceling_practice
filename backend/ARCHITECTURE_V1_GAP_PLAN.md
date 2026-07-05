# V1 Architecture Gap Plan

This project is moving from a prompt-driven counseling simulator toward the
stateful, versioned architecture described in
`AI_Counseling_Simulator_Coding_Agent_Spec.md`.

## Architecture Spine Added First

- `app/scenario_templates/` defines developer-owned template families.
- `microskills_progressive_disclosure` is the initial V1 template.
- `scenario_versions` stores immutable published snapshots.
- `simulation_sessions.scenario_version_id` pins a student attempt to a
  specific published version.
- `session_states` stores engagement, trust, disclosure stage, revealed
  information, emotional cues, session stage, and state history.

## Current Integration Boundary

New sessions now create an initial state row and can reference a scenario
version when the scenario has one. Each student turn is locally classified,
applies deterministic engagement/disclosure transitions, and appends runtime
state context to the Gemini client prompt.

Evaluation now consumes `scenario_versions` and `session_states` when available:
the evaluator prompt receives template metadata, learning objectives, rubric
snapshots, and state history. The student-facing response still preserves the
original Module 1 score fields so the current frontend remains compatible.

## Next Backend Phases

1. Complete the flexible evaluation envelope.
   - Replace fixed `RubricScores` with dynamic criteria once the frontend can
     render arbitrary rubric items.
   - Expand specialized analyses: emotional exploration, engagement
     progression, disclosure progression, and question/reflection balance.
   - Surface missed opportunities and faculty-review recommendation in reports.

2. Update faculty test mode.
   - Persist or simulate a test-session state.
   - Show debug engagement, disclosure stage, allowed disclosures, and state
     events only to faculty.

3. Replace the local classifier with a Gemini-backed classifier.
   - Keep the current deterministic classifier as a safe fallback.
   - Validate Gemini output against the existing behavior-label schema.

## Frontend Contract Changes Still Needed

- Scenario summaries/details should expose template metadata and current version.
- Session details should expose `scenario_version_id`.
- Faculty test chat should display debug state.
- Feedback reports should render dynamic rubric criteria instead of fixed
  Module 1 score fields.
