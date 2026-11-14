# SmartDoctor AI Agents and LangGraph Orchestration

## 1. Design

Use a supervisor/orchestrator that invokes narrowly scoped agents through typed interfaces. Agents do not grant themselves access, change permissions, diagnose, prescribe, sign clinical records or perform uncontrolled external writes.

The orchestrator is responsible for state transitions, policy checks, retry limits, timeouts, persistence and human-review pauses.

## 2. Agent catalogue

| Agent/service | Responsibility | Allowed output |
|---|---|---|
| Language detector | Detect current message language | Language code and confidence |
| Intent classifier | Categorize the request | Validated intent schema |
| Safety screening | Apply approved warning-sign rules and escalation logic | Flags, rule IDs and next safe action |
| Patient context | Fetch authorized, relevant records | Provenance-tagged context |
| Symptom assessment | Organize reported symptoms and ask focused questions | Structured patient-reported assessment |
| Medical knowledge | Retrieve approved evidence | Ranked passages and citations |
| Lab report | Extract and explain validated report values | Candidate/extracted result schema |
| Medication information | Retrieve trusted drug information | Source-backed medication facts |
| Medical history | Summarize authorized records | Dated, source-linked summary |
| Nutrition education | Explain approved general nutrition information | Educational response with limits |
| Doctor handoff | Prepare a review packet | Draft handoff summary |
| Response composer | Convert validated facts into accessible language | Patient-facing draft |
| Audit/evaluation | Record model and workflow metadata | Audit event and evaluation result |

Safety screening should include deterministic rules and an independently evaluated classifier where appropriate. Do not treat an LLM's risk label as the sole emergency control.

## 3. Routing

```text
START
  -> authenticate and authorize
  -> language detection
  -> intent classification
  -> independent safety screening
       -> emergency: emergency guidance and stop routine flow
       -> routine: context policy check
            -> symptom assessment
            -> report analysis
            -> medication information
            -> medical history
            -> general medical knowledge
            -> appointment / handoff
  -> evidence and output validation
  -> response composition
  -> audit and persist
END
```

The router must reject unknown intents and fall back to a safe clarification or human route. Tool access is allowlisted per agent and per workflow.

## 4. Typed workflow state

Example conceptual state (implementation should use Pydantic models and explicit optional/nullable fields):

```python
from typing import Literal
from pydantic import BaseModel, Field

class EvidenceItem(BaseModel):
    source_id: str
    title: str
    excerpt: str
    source_date: str | None = None
    source_type: str
    confidence: float | None = Field(default=None, ge=0, le=1)

class DoctorBotState(BaseModel):
    conversation_id: str
    authenticated_user_id: str
    patient_id: str | None = None
    organization_id: str | None = None
    language: str | None = None
    intent: str | None = None
    risk_flags: list[str] = []
    workflow_status: Literal[
        "started", "awaiting_patient", "awaiting_clinician",
        "completed", "blocked", "failed"
    ] = "started"
    authorized_context: dict = {}
    patient_reported_facts: list[dict] = []
    evidence: list[EvidenceItem] = []
    agent_outputs: dict = {}
    response_draft: str | None = None
    requires_clinician_review: bool = False
    errors: list[str] = []
```

In production, use immutable or carefully copied state updates; do not share mutable defaults. Keep access tokens and raw credentials out of graph state. Persist only what is required and apply retention controls.

## 5. Agent contract

Each agent should expose:
- Typed input and output schema.
- Purpose and allowed workflow list.
- Required permissions and data classification.
- Allowed tools and external destinations.
- Timeout, retry and token budgets.
- Failure and safe fallback behavior.
- Prompt/model version.
- Evaluation suite and release status.

An agent returns facts, evidence, uncertainty and recommendations for the next workflow step. It does not directly send patient-visible content unless the response policy permits it.

## 6. Tool permissions

| Tool | Allowed callers |
|---|---|
| Read patient profile | Patient-context workflow after access check |
| Read EHR resources | Integration adapter with scoped consent/token |
| Search approved medical corpus | Medical knowledge agent |
| Read patient document | Report/context workflow after patient authorization |
| Extract report text | Document-processing worker |
| Create clinician handoff | Handoff workflow after policy check |
| Write signed clinical note | Clinician-authorized API only |
| Prescribe/change medication | Not available to AI agents |

## 7. Human-in-the-loop checkpoints

Require clinician review for any feature designated as clinical decision support, any clinical note intended for the record, ambiguous or low-confidence extraction that could affect care, and any future regulated action. Human review must present source evidence, uncertainty and the exact proposed action.

## 8. Operational limits

- Bound graph recursion and total execution time.
- Use idempotency keys for side-effecting tools.
- Do not automatically retry non-idempotent clinical writes.
- Persist checkpoints for long-running workflows.
- Redact sensitive values from traces.
- Use circuit breakers for external systems.
- Record model and prompt versions on every AI run.
