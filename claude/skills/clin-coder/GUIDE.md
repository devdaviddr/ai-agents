# clin-coder — usage guide (worked examples)

Hands-on examples of the **clin-coder** skill and its companion agents, with real inputs and expected
outputs. Everything runs on the bundled **synthetic** data.

- Skill: [`clin-coder`](SKILL.md) · Agents: [`clin-coder-concept-extractor`](../../agents/clin-coder-concept-extractor.md) · [`clin-coder-verifier`](../../agents/clin-coder-verifier.md) · [`clin-coder-cdi`](../../agents/clin-coder-cdi.md)
- Repo: **https://github.com/devdaviddr/ai-resources** · this skill: **https://github.com/devdaviddr/ai-resources/tree/main/claude/skills/clin-coder**

> [!IMPORTANT]
> Synthetic and advisory only. Codes/standards are fictional (SCC/SCS — not ICD-10-AM/ACHI/ACS). Output is
> a proposal for a qualified human coder, never automated billing/funding.

## Install (once)

```bash
git clone https://github.com/devdaviddr/ai-resources.git && cd ai-resources
./scripts/link.sh --global      # or ./scripts/link.sh to use inside the repo only
claude                          # launch Claude Code
```

The three pieces:
- **Skill** — invoke in conversation with `/clin-coder` (or "code this episode").
- **Agents** — delegated workers Claude calls (or you name): `concept-extractor`, `verifier`, `cdi`.
- **Engine** — the bundled `scripts/ccagent.py`, which the skill/agents call for deterministic steps.

---

## Example 1 — Skill: code an episode (negation + family-history traps)

**Input** (in Claude Code, with an example episode that documents things it then *rules out*):

```
/clin-coder code the example episode EP-0004
```

Behind the scenes the skill screens the note's context first:

```
$ ccagent.py context --from assets/examples/episodes/EP-0004-negation-family.md
['historical'] :: ...productive cough on a background of COPD
['negated']    :: Denies chest pain
['negated']    :: no evidence of pneumonia
['family','historical'] :: Family history of colon cancer (father)
['negated']    :: acute coronary syndrome ruled out
```

**Expected output** — a proposal that codes the exacerbation + infection and **withholds** everything
negated or family-history:

```json
{
  "episode_id": "EP-0004",
  "principal_diagnosis": { "code": "DX-RESP-001", "condition_onset_flag": 1,
    "evidence_span": "Impression: infective exacerbation of COPD", "scs_basis": ["SCS-0001"] },
  "additional_diagnoses": [
    { "code": "DX-INFX-001", "condition_onset_flag": 1,
      "evidence_span": "intravenous antibiotics for a bacterial chest infection",
      "scs_basis": ["SCS-0002", "SCS-MULT-01"] }
  ],
  "procedures": [],
  "not_coded": [
    { "concept": "Pneumonia", "candidate_code": "DX-RESP-010", "reason": "'no evidence of pneumonia'", "scs_basis": ["SCS-NEG-01"] },
    { "concept": "Chest pain", "candidate_code": "DX-SYMP-001", "reason": "'denies chest pain'", "scs_basis": ["SCS-NEG-01"] },
    { "concept": "NSTEMI", "candidate_code": "DX-CARD-001", "reason": "ruled out", "scs_basis": ["SCS-NEG-01"] },
    { "concept": "Colon cancer", "candidate_code": "DX-NEO-001", "reason": "family history only", "scs_basis": ["SCS-FAM-01"] }
  ],
  "predicted_ar_drg": { "code": "S-DRG-E65B", "description": "(synthetic) MDC 04, complexity B" }
}
```

The payoff: four documented-but-non-codeable concepts are correctly **left out** — the #1 over-coding trap.

---

## Example 2 — Skill: symptom vs definitive diagnosis

**Input:**

```
/clin-coder code EP-0002
```

The note presents with *chest pain* but establishes *NSTEMI* after study.

**Expected output** (abridged): principal is the **diagnosis**, not the symptom — and the symptom is
withheld under SCS-SEQ-01:

```json
{
  "principal_diagnosis": { "code": "DX-CARD-001", "evidence_span": "Diagnosis: NSTEMI", "scs_basis": ["SCS-0001","SCS-SEQ-01"] },
  "additional_diagnoses": [ { "code": "DX-ELEC-001", "evidence_span": "K 3.0 ... IV potassium", "scs_basis": ["SCS-0002"] } ],
  "procedures": [ { "code": "PX-CARD-002" }, { "code": "PX-CARD-001" } ],
  "not_coded": [ { "concept": "Chest pain", "candidate_code": "DX-SYMP-001", "reason": "superseded by NSTEMI", "scs_basis": ["SCS-SEQ-01"] } ],
  "predicted_ar_drg": { "code": "S-DRG-F41B" }
}
```

---

## Example 3 — Agent `clin-coder-concept-extractor`

Use one per document to pull concepts **with clinical context** (what makes downstream withholding possible).

**Input** (a single document handed to the agent):

```
CXR reviewed: no evidence of pneumonia. Denies chest pain. Impression: infective exacerbation of COPD.
Family history of colon cancer (father).
```

**Expected output** (its final message is JSON only):

```json
{
  "document_type": "discharge_summary",
  "concepts": [
    { "concept": "pneumonia", "kind": "diagnosis", "evidence_span": "no evidence of pneumonia", "certainty": "negated", "temporality": "current", "attribution": "patient", "onset": "unclear" },
    { "concept": "chest pain", "kind": "finding", "evidence_span": "Denies chest pain", "certainty": "negated", "temporality": "current", "attribution": "patient", "onset": "unclear" },
    { "concept": "infective exacerbation of COPD", "kind": "diagnosis", "evidence_span": "Impression: infective exacerbation of COPD", "certainty": "confirmed", "temporality": "current", "attribution": "patient", "onset": "present_on_admission" },
    { "concept": "colon cancer", "kind": "diagnosis", "evidence_span": "Family history of colon cancer (father)", "certainty": "confirmed", "temporality": "historical", "attribution": "family", "onset": "unclear" }
  ],
  "ambiguities": []
}
```

Only the COPD concept is `confirmed / patient / current` — the rest carry flags that make them non-codeable.

---

## Example 4 — Agent `clin-coder-verifier`

Audits a proposal before a coder sees it. It runs the engine's deterministic checks **and** reasons about
whether each code is clinically justified.

**Input:** a proposal that over-codes the negated pneumonia
([`sample-proposals/EP-0004.json`](assets/examples/sample-proposals/EP-0004.json)).

The deterministic checks alone *pass* (the code exists and has an evidence span):

```
$ ccagent.py verify --from assets/examples/sample-proposals/EP-0004.json
PASS  principal   DX-RESP-001
PASS  additional  DX-INFX-001
PASS  additional  DX-RESP-010
3 code(s), 0 failing.
```

…which is exactly why the agent adds value — it reads the evidence critically and **rejects** the
over-code the deterministic gate can't catch:

**Expected output:**

```json
{
  "overall": "fail",
  "edits": "0 fail, 0 warn",
  "verdicts": [
    { "code": "DX-RESP-001", "role": "principal", "verdict": "confirmed", "reason": "impression documents an infective exacerbation of COPD" },
    { "code": "DX-INFX-001", "role": "additional", "verdict": "confirmed", "reason": "IV antibiotics for a bacterial chest infection" },
    { "code": "DX-RESP-010", "role": "additional", "verdict": "reject", "reason": "pneumonia is explicitly negated ('no evidence of pneumonia') — SCS-NEG-01; the cited span 'productive cough' does not support a pneumonia code" }
  ],
  "notes": ["Over-coding: a negated finding was coded. Withholding check would fail (see `ccagent.py check`)."]
}
```

Running the score confirms it: `check` reports **withholding 3/4** and precision 0.67 for this proposal.

---

## Example 5 — Agent `clin-coder-cdi`

When the record implies a condition but doesn't document it, draft a **non-leading** clarification query.

**Input:**

```
Potassium 2.9 mmol/L on day 1, replaced with IV potassium. (No diagnosis of hypokalaemia documented.)
```

**Expected output:**

```json
{
  "queries": [
    {
      "gap": "Low potassium was treated but no diagnosis is documented.",
      "evidence": "Potassium 2.9 mmol/L on day 1, replaced with IV potassium",
      "question": "The record shows potassium replacement for a low serum potassium. If clinically significant, can the diagnosis be documented?",
      "options": ["Hypokalaemia", "Electrolyte abnormality, not otherwise specified", "Not clinically significant / unable to determine"],
      "why_it_matters": "A documented, treated diagnosis may be codeable as an additional diagnosis (SCS-0002); without documentation it cannot be coded."
    }
  ]
}
```

Note the neutral options including "not clinically significant" — the query never leads toward a
higher-complexity code.

---

## Example 6 — the engine directly (deterministic tools)

You can drive the bundled engine yourself. Real outputs:

```
$ ccagent.py index diabetes
Diabetes, mellitus
    - type 1, with ketoacidosis: DX-ENDO-002
    - type 2, without complications: DX-ENDO-001
    - type 2, with chronic kidney disease: DX-ENDO-003
    - type 2, with diabetic nephropathy (combination): DX-COMB-001
    - with cataract (dagger): DX-EYE-DAG

$ ccagent.py validate DX-RESP-001 DX-FAKE-9
OK       DX-RESP-001  Chronic obstructive pulmonary disease with acute lower respiratory infection
INVALID  DX-FAKE-9    <- not in code set          # exit code 1

$ ccagent.py edits --from <proposal-with-errors>
FAIL  principal DX-EYE-AST is not an acceptable principal diagnosis (symptom/asterisk) — SCS-EDIT-01
FAIL  DX-OBS-001 is sex-specific (F) but patient sex is M — SCS-EDIT-01

$ ccagent.py eval
episode             P    R   F1  pdx drg hall  grounded  withheld
EP-0001           1.0  1.0  1.0    Y   Y    0       3/3       1/1
EP-0002          0.75 0.75 0.75    Y   Y    0       2/2       0/1
EP-0004          0.67  1.0  0.8    Y   Y    0       3/3       3/4
macro F1=0.85  principal-dx acc=1.00  DRG acc=1.00  total hallucinations=0
```

## Which check catches what

| Tool | Catches |
|------|---------|
| `context` | Findings that must not be coded — negated / historical / family / (untreated) uncertain |
| `validate` | Non-existent (hallucinated) codes |
| `edits` | Invalid codings — unacceptable principal, sex conflict, excludes clash, missing code-also, dagger/asterisk, combination, morphology |
| `verify` | Codes lacking an evidence span or rule citation |
| `check` / `eval` | Accuracy vs a gold coding — precision/recall/F1, principal-dx, DRG, **over-coding via withholding** |
| `clin-coder-verifier` (agent) | Clinically wrong-but-well-formed codes the deterministic checks pass (e.g. a negated finding coded) |

---

More detail: [SKILL.md](SKILL.md) · [README.md](README.md) · repo: https://github.com/devdaviddr/ai-resources
