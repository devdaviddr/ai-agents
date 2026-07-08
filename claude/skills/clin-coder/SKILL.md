---
name: clin-coder
description: Propose clinical codes for a patient episode against a bundled synthetic code set and coding standards — principal + additional diagnoses with condition-onset flags, procedures, and a predicted AR-DRG, each grounded to an evidence span in the note and a rule citation. Never emits an unvalidated code; flags ambiguity for a human coder instead of guessing. Use when asked to code an episode, discharge summary, or clinical note. Trigger on "/clin-coder" or "code this episode".
allowed-tools: Read, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)
---

# clin-coder — agentic clinical coding on synthetic data

Turn a patient's episode documentation into an **auditable coding proposal**: principal diagnosis,
additional diagnoses (with condition-onset flags), procedures, and a predicted group — every code tied
to *a sentence in the note* and *the rule that governs it*.

> [!IMPORTANT]
> **Synthetic and advisory only.** The bundled code set is a made-up **Synthetic Clinical Classification
> (SCC)** and the rules a made-up **Synthetic Coding Standards (SCS)** — NOT ICD-10-AM/ACHI/ACS (copyright
> IHACPA), NOT medical/coding advice. Output is a proposal for a **qualified human coder** to review —
> never an automated billing or funding decision.

The deterministic helper is **bundled** and pure-Python (stdlib only). Invoke it via the skill-dir
variable so it resolves at any install scope:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ccagent.py" catalog     # code set + standards summary
python3 "${CLAUDE_SKILL_DIR}/scripts/ccagent.py" example     # list bundled example episodes
```

**Core principle:** the model decides *what the episode says*; the script keeps *codes real and grouping
deterministic*. Never emit a code the script hasn't validated.

## Workflow

1. **Get the episode.** Read the note the user points at. To demo, use a bundled example:
   `python3 "${CLAUDE_SKILL_DIR}/scripts/ccagent.py" example EP-0001`.

2. **Load the standards.** `ccagent.py catalog`, and read `reference/scs-rules.json` for the rule text.
   Assign each documented condition/procedure to the standards you'll apply.
   (For a long or multi-document episode, delegate concept extraction to the **`clin-coder-concept-extractor`**
   subagent — one per document, in parallel — and collect the concepts + evidence spans it returns.)

3. **Map concepts to candidate codes.** For each clinical concept, `ccagent.py lookup "<term>"` to get
   candidates, then choose. Honour the code's classification instructions in `reference/` (`excludes`,
   `code_also`, `code_first`).

4. **Validate — never skip this.** `ccagent.py validate CODE...`. If any code is INVALID, do not emit it;
   go back to `lookup`. This is the zero-hallucination gate.

5. **Apply the coding standards (SCS):**
   - **Principal diagnosis (SCS-0001)** — the condition chiefly responsible for the episode. If the reason
     for admission was a symptom but a definitive diagnosis was established, code the diagnosis, not the
     symptom (**SCS-SEQ-01**).
   - **Additional diagnoses (SCS-0002)** — include a comorbidity/complication only if it was treated,
     investigated, monitored, or extended the stay. Otherwise leave it out (say so in the proposal).
   - **Condition-onset flag (SCS-COF-01)** — 1 = present on admission, 2 = arose during the episode.
   - **Code also (SCS-MULT-01)** — follow `code_also` instructions to add linked codes.

6. **Group.** Write your draft proposal to a temp file (schema below) and run
   `ccagent.py group --from /tmp/proposal.json` for the predicted (synthetic) AR-DRG.

7. **Verify.** `ccagent.py verify --from /tmp/proposal.json` — confirms every code is real and carries an
   evidence span + rule citation. (For an independent audit, delegate to the **`clin-coder-verifier`**
   subagent — a read-only reviewer that cannot alter the proposal.) Drop anything that fails; **flag**
   low-confidence or contradictory items as coder queries rather than guessing.

8. **Present.** Show the coder a readable summary (each code → its evidence span → its SCS citation →
   confidence) plus the JSON proposal. List anything you deliberately did **not** code and why. Do not
   mark anything approved — that's the human's call.

9. **(Optional) Evaluate.** For a bundled example, score against its gold coding:
   `ccagent.py check --proposal /tmp/proposal.json --gold "${CLAUDE_SKILL_DIR}/assets/examples/gold/EP-0001.json"`.

## Proposal schema

```json
{
  "episode_id": "EP-XXXX",
  "principal_diagnosis": { "code": "", "condition_onset_flag": 1, "evidence_span": "", "scs_basis": ["SCS-0001"] },
  "additional_diagnoses": [
    { "code": "", "condition_onset_flag": 1, "evidence_span": "", "scs_basis": ["SCS-0002"], "rationale": "" }
  ],
  "procedures": [ { "code": "", "evidence_span": "" } ],
  "not_coded": [ { "concept": "", "candidate_code": "", "reason": "", "scs_basis": ["SCS-0002"] } ],
  "predicted_ar_drg": { "code": "", "description": "" }
}
```

## What's bundled

- `scripts/ccagent.py` — `catalog · codes · lookup · validate · group · verify · check · example`.
- `reference/` — the SCC code set (`scc-diagnoses.json`, `scc-procedures.json`) + SCS rules (`scs-rules.json`).
- `assets/examples/` — 3 fictional episodes + their gold codings (COPD+T2DM, chest-pain→NSTEMI, DKA+AKI),
  seeded with hard cases: additional-dx that fails SCS-0002, symptom-vs-definitive, hospital-acquired
  onset flags, and `code_also` chains.

## Companion subagents (optional, in this collection)

- **`clin-coder-concept-extractor`** — read-only, one per document, parallel: extracts concepts + evidence spans.
- **`clin-coder-verifier`** — read-only auditor that runs `ccagent.py verify` and cannot modify the proposal.

They compose with this skill; if not installed, do steps 2 and 7 inline.
