---
name: clin-coder
description: Propose clinical codes for a patient episode against a bundled synthetic code set and coding standards — principal + additional diagnoses with condition-onset flags, procedures, and a predicted AR-DRG, each grounded to an evidence span in the note and a rule citation. Screens out negated/historical/family findings, enforces validity edits, never emits an unvalidated code, and flags ambiguity for a human coder instead of guessing. Use when asked to code an episode, discharge summary, or clinical note. Trigger on "/clin-coder" or "code this episode".
allowed-tools: Read, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)
---

# clin-coder — agentic clinical coding on synthetic data

**What this is:** a skill that turns a patient's episode documentation into an **auditable coding
proposal** — principal diagnosis, additional diagnoses (with condition-onset flags), procedures, and a
predicted funding group — with every code tied to *a sentence in the note* and *the coding-standard rule*
that governs it, for a **human coder** to review.

> [!IMPORTANT]
> **Synthetic and advisory only.** The bundled code set is a made-up **Synthetic Clinical Classification
> (SCC)** and the rules a made-up **Synthetic Coding Standards (SCS)** — NOT ICD-10-AM/ACHI/ACS (copyright
> IHACPA), NOT medical/coding advice. Output is a proposal for a qualified human coder, never an automated
> billing/funding decision.

**Core principle:** the model decides *what the episode says*; the bundled script keeps *codes real,
edits enforced, and grouping deterministic*. Never emit a code the script hasn't validated.

The helper is bundled, pure-Python (stdlib only). Invoke via the skill-dir variable:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/ccagent.py" catalog     # code set + standards summary
python3 "${CLAUDE_SKILL_DIR}/scripts/ccagent.py" example     # list bundled example episodes
```

## Workflow

1. **Get the episode.** Read the note the user points at, or a bundled example
   (`ccagent.py example EP-0001`).

2. **Screen the documentation context — do this before coding.**
   `ccagent.py context --from <note>` runs a negation/uncertainty/history/family screen. **Do not code**
   findings that are **negated** ("no evidence of…", "denies…", "ruled out") — SCS-NEG-01 — **historical**
   ("history of…") unless treated this episode — SCS-HX-01 — or attributed to a **family member** —
   SCS-FAM-01. An **uncertain** diagnosis ("probable…") is coded only if it was *treated as such* —
   SCS-UNC-01. (For long/multi-document episodes, delegate extraction to the **`clin-coder-concept-extractor`**
   subagent, which returns concepts with these context flags.)

3. **Load the standards.** `ccagent.py catalog` + read `reference/scs-rules.json`.

4. **Map concepts to codes.** Navigate the alphabetic index (`ccagent.py index "<lead term>"`) and/or
   `ccagent.py lookup "<term>"` for candidates. Honour each code's instructions (`excludes`, `code_also`,
   `code_first`), and prefer a **combination code** over coding components separately (SCS-COMB-01).

5. **Validate — never skip.** `ccagent.py validate CODE...`. Any INVALID code is dropped; go back to step 4.

6. **Apply the coding standards (SCS):**
   - **Principal (SCS-0001)** — the condition chiefly responsible for the episode; if a symptom was the
     presenting complaint but a definitive diagnosis was established, code the diagnosis (**SCS-SEQ-01**).
   - **Additional (SCS-0002)** — include only if treated, investigated, monitored, or it extended the stay.
   - **Condition-onset flag (SCS-COF-01)** — 1 = present on admission, 2 = arose during the episode.
   - **Dual coding (SCS-DAG-01)** — dagger first, then asterisk; **morphology (SCS-MORPH-01)** with a neoplasm.

7. **Group.** Write the draft proposal (schema below) to a temp file and run
   `ccagent.py group --from /tmp/proposal.json` for the predicted (synthetic) group + complexity.

8. **Run validity edits.** `ccagent.py edits --from /tmp/proposal.json` — checks unacceptable principal,
   sex conflicts, `excludes` clashes, missing `code_also`, dagger/asterisk pairing, combination
   supersession, and morphology. Fix every FAIL; resolve WARNs.

9. **Verify grounding.** `ccagent.py verify --from /tmp/proposal.json` — every code real + carrying an
   evidence span + rule citation. (Or delegate to the read-only **`clin-coder-verifier`** subagent.)

10. **Flag, don't guess.** Anything ambiguous, contradictory, or under-documented becomes a **coder
    query** — not a silent code. If documentation is too thin to code confidently, use the
    **`clin-coder-cdi`** subagent to draft a documentation-improvement query.

11. **Present.** Give the coder a readable summary (each code → evidence span → SCS citation →
    confidence), the JSON proposal, the predicted group, and the list of what you did **not** code and
    why. **Do not mark anything approved** — that is the human's decision.

12. **(Optional) Evaluate.** For bundled examples, score against gold:
    `ccagent.py check --proposal /tmp/proposal.json --gold "${CLAUDE_SKILL_DIR}/assets/examples/gold/EP-0001.json"`,
    or the whole batch: `ccagent.py eval`.

## Proposal schema

```json
{
  "episode_id": "EP-XXXX",
  "patient": { "sex": "M", "age": 68 },
  "principal_diagnosis": { "code": "", "condition_onset_flag": 1, "evidence_span": "", "scs_basis": ["SCS-0001"] },
  "additional_diagnoses": [
    { "code": "", "condition_onset_flag": 1, "evidence_span": "", "scs_basis": ["SCS-0002"], "rationale": "" }
  ],
  "procedures": [ { "code": "", "evidence_span": "" } ],
  "not_coded": [ { "concept": "", "candidate_code": "", "reason": "", "scs_basis": ["SCS-NEG-01"] } ],
  "predicted_ar_drg": { "code": "", "description": "" }
}
```

## Engine reference (`scripts/ccagent.py`)

`catalog` · `codes [q]` · `index [lead term]` · `lookup <term>` · `context --from <note> [--term t]` ·
`validate <code…>` · `edits --from <proposal>` · `group --from <proposal>` · `verify --from <proposal>` ·
`check --proposal <p> --gold <g>` · `eval [--proposals DIR --gold DIR]` · `example [id]`.

## What's bundled

- `reference/` — the SCC code set (`scc-diagnoses.json` + `scc-procedures.json`), the SCS rules
  (`scs-rules.json`), and the alphabetic index (`scc-index.json`).
- `assets/examples/` — 6 fictional episodes + gold codings, plus `sample-proposals/` (one perfect, two
  with deliberate errors) so `eval` produces a live scoreboard.
- `scripts/ccagent.py` — the stdlib-only engine above.

## Companion subagents (optional, in this collection)

- **`clin-coder-concept-extractor`** — read-only, one per document, parallel: concepts + evidence spans + context flags.
- **`clin-coder-verifier`** — read-only auditor: runs `edits`/`verify`, cannot modify the proposal.
- **`clin-coder-cdi`** — read-only: drafts a clinical-documentation-improvement query when the note is too thin to code.

They compose with this skill; if not installed, do those steps inline.

## Scope / reality-check

This is a **demonstration on synthetic data**, not a production coder. It deliberately does **not** include
the real ICD-10-AM/ACHI/ACS content or a licensed AR-DRG grouper (IHACPA licensing), EMR/PAS integration,
OCR / real-document ingestion + de-identification, or a coder-validated evaluation. Those are out of scope
for a skill and would be a separate, governed build.
