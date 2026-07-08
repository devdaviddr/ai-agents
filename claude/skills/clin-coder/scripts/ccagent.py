#!/usr/bin/env python3
"""ccagent.py — deterministic engine for the clin-coder skill (stdlib only).

Tools over a SYNTHETIC code set + coding standards. EVERYTHING HERE IS FICTIONAL:
codes are a made-up Synthetic Clinical Classification (SCC) and rules a made-up Synthetic
Coding Standards (SCS) — NOT ICD-10-AM/ACHI/ACS (copyright IHACPA), NOT medical/coding advice.
The model reasons about the note; this script keeps codes real, edits enforced, grouping
deterministic, and scoring objective.

Subcommands
  catalog                          summarise the code set + standards
  codes [QUERY]                    list/search the tabular code set
  index [LEAD TERM]                navigate the alphabetic index (lead term -> code)
  lookup TERM...                   fuzzy-map a clinical term to candidate codes
  context --from NOTE [--term T]   NegEx/ConText-style screen: negation / uncertainty /
                                   history / family context around findings
  validate CODE...                 check codes exist (exit 1 if any don't)
  edits  --from PROPOSAL.json      validity edits: unacceptable principal, sex, excludes,
                                   code-also, dagger/asterisk, combination, morphology
  group  --from PROPOSAL.json      MDC + complexity -> predicted (synthetic) AR-DRG
  verify --from PROPOSAL.json      every code real + grounded (evidence + rule)?
  check  --proposal P --gold G     score one proposal against a gold coding
  eval   [--proposals DIR --gold DIR]   batch scoreboard over all episodes
  example [ID]                     print an example episode note (default: list them)
"""
import sys, os, json, argparse, difflib, re, glob

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(SKILL_DIR, "reference")
EX = os.path.join(SKILL_DIR, "assets", "examples")

SEV_WEIGHT = {"catastrophic": 4.0, "severe": 2.0, "minor": 0.5, None: 0.5}
# base DRG letter per MDC (synthetic)
BASE_DRG = {
    "DX-RESP-001": "E65", "DX-RESP-002": "E65", "DX-RESP-010": "E62", "DX-RESP-005": "E69",
    "DX-CARD-001": "F41", "DX-CARD-002": "F74", "DX-ENDO-002": "K60", "DX-ENDO-001": "K60",
    "DX-ENDO-003": "K60", "DX-COMB-001": "K60", "DX-RENAL-001": "L63", "DX-NEO-001": "G02",
    "DX-OBS-001": "O60", "DX-GU-001": "L40",
}

# ---------- loaders ----------
def load_codes():
    codes = {}
    for fn in ("scc-diagnoses.json", "scc-procedures.json"):
        with open(os.path.join(REF, fn)) as f:
            for c in json.load(f).get("codes", []):
                codes[c["code"]] = c
    return codes

def load_rules():
    with open(os.path.join(REF, "scs-rules.json")) as f:
        return {r["id"]: r for r in json.load(f).get("rules", [])}

def load_index():
    with open(os.path.join(REF, "scc-index.json")) as f:
        return json.load(f).get("lead_terms", {})

def _load(path):
    with open(path) as f:
        return json.load(f)

def _codes_in(obj):
    if isinstance(obj, list):
        return [c if isinstance(c, str) else c.get("code") for c in obj]
    out = []
    if obj.get("principal_diagnosis"):
        out.append(obj["principal_diagnosis"].get("code"))
    out += [d.get("code") for d in obj.get("additional_diagnoses", [])]
    out += [p.get("code") for p in obj.get("procedures", [])]
    return [c for c in out if c]

def _dx_items(obj):
    items = []
    if obj.get("principal_diagnosis"):
        items.append(("principal", obj["principal_diagnosis"]))
    items += [("additional", d) for d in obj.get("additional_diagnoses", [])]
    return items

# ---------- catalog / browse ----------
def cmd_catalog(a):
    codes, rules = load_codes(), load_rules()
    chapters = {}
    for c in codes.values():
        ch = c.get("chapter") or c.get("block") or "?"
        chapters[ch] = chapters.get(ch, 0) + 1
    print(f"SCC code set: {len(codes)} codes (SYNTHETIC — not ICD-10-AM/ACHI)")
    for ch, n in sorted(chapters.items()):
        print(f"  {ch}: {n}")
    print(f"\nSCS standards: {len(rules)} rules (SYNTHETIC — not the real ACS)")
    for rid, r in rules.items():
        print(f"  {rid}  {r['title']}")

def cmd_codes(a):
    codes = load_codes()
    q = (a.query or "").lower()
    for code, c in sorted(codes.items()):
        if not q or q in code.lower() or q in c["description"].lower():
            instr = c.get("instructions") or {}
            flags = [k for k in ("excludes", "code_also", "code_first") if instr.get(k)]
            for extra in ("unacceptable_principal", "dagger", "morphology_required", "sex", "supersedes"):
                if c.get(extra):
                    flags.append(extra if not isinstance(c[extra], str) else f"{extra}={c[extra]}")
            print(f"{code:14} {c['description']}" + (f"   [{', '.join(flags)}]" if flags else ""))

def cmd_index(a):
    idx = load_index()
    term = (a.term or "").lower()
    hits = {lt: subs for lt, subs in idx.items() if not term or term in lt.lower()}
    if not hits:
        print(f"No lead term matching {a.term!r}. Try `index` with no argument to list lead terms.")
        return
    for lt, subs in sorted(hits.items()):
        print(lt)
        for sub, code in subs.items():
            print(f"    - {sub or '(default)'}: {code}")

def cmd_lookup(a):
    codes = load_codes()
    term = " ".join(a.term).lower()
    scored = []
    for code, c in codes.items():
        s = difflib.SequenceMatcher(None, term, c["description"].lower()).ratio()
        if term in c["description"].lower():
            s += 0.4
        scored.append((round(s, 3), code, c["description"]))
    scored.sort(reverse=True)
    for s, code, desc in scored[:8]:
        print(f"{s:>5}  {code:14} {desc}")

# ---------- clinical-NLP context screen (NegEx/ConText-lite) ----------
NEG_CUES = ["no evidence of", "no sign of", "negative for", "denies", "denied", "ruled out",
            "rule out", "without", "absence of", "absent", "not ", "no ", "free of", "resolved"]
UNC_CUES = ["query", "?", "possible", "possibly", "probable", "probably", "likely", "suspected",
            "suspicious for", "cannot exclude", "can't exclude", "differential", " vs ", "vs.", "r/o"]
HX_CUES = ["history of", "hx of", "h/o", "previous", "prior", "past history", "ex-", "old ",
           "background of", "known "]
FAM_CUES = ["family history", "fhx", "father", "mother", "brother", "sister", "sibling",
            "parent", "familial", "maternal", "paternal"]

def _sentences(text):
    return [s.strip() for s in re.split(r"[.\n;]+", text) if s.strip()]

def _classify(sentence):
    s = " " + sentence.lower() + " "
    flags = []
    if any(c in s for c in FAM_CUES):
        flags.append("family")
    if any(c in s for c in HX_CUES):
        flags.append("historical")
    if any(c in s for c in NEG_CUES):
        flags.append("negated")
    if any(c in s for c in UNC_CUES):
        flags.append("uncertain")
    return flags or ["affirmed"]

def cmd_context(a):
    text = open(a.from_file).read()
    sents = _sentences(text)
    out = []
    term = (a.term or "").lower()
    for s in sents:
        if term and term not in s.lower():
            continue
        flags = _classify(s)
        if term or flags != ["affirmed"]:
            out.append({"flags": flags, "sentence": s})
    codeable = [o for o in out if not ({"negated", "historical", "family"} & set(o["flags"]))]
    print(json.dumps({
        "note": "SYNTHETIC NegEx/ConText-lite screen. 'negated'/'historical'/'family' findings are NOT codeable (SCS-NEG-01/HX-01/FAM-01); 'uncertain' may be codeable only if treated as such (SCS-UNC-01).",
        "term": a.term, "hits": out,
        "guidance": f"{len(codeable)}/{len(out)} matched sentence(s) look codeable" if out else "no cued findings"
    }, indent=2))

# ---------- validate ----------
def cmd_validate(a):
    codes = load_codes()
    bad = []
    for code in a.code:
        ok = code in codes
        print(f"{'OK ' if ok else 'INVALID'}  {code}" + (f"  {codes[code]['description']}" if ok else "  <- not in code set"))
        if not ok:
            bad.append(code)
    if bad:
        print(f"\n{len(bad)} invalid code(s) — do not emit these.", file=sys.stderr)
        sys.exit(1)

# ---------- validity edits ----------
def cmd_edits(a):
    codes = load_codes()
    obj = _load(a.from_file)
    present = set(_codes_in(obj))
    patient = obj.get("patient", {})
    fails, warns = [], []

    pdx = (obj.get("principal_diagnosis") or {}).get("code")
    if pdx in codes and codes[pdx].get("unacceptable_principal"):
        fails.append(f"principal {pdx} is not an acceptable principal diagnosis (symptom/asterisk) — SCS-EDIT-01")

    for code in present:
        c = codes.get(code)
        if not c:
            fails.append(f"{code} not in code set (hallucination)")
            continue
        if c.get("sex") and patient.get("sex") and c["sex"] != patient["sex"]:
            fails.append(f"{code} is sex-specific ({c['sex']}) but patient sex is {patient['sex']} — SCS-EDIT-01")
        for ex in (c.get("instructions") or {}).get("excludes", []):
            if ex in present:
                fails.append(f"{code} excludes {ex} but both are present — SCS-EDIT-01")
        for req in (c.get("instructions") or {}).get("code_also", []):
            if req.startswith("DX-") and req not in present:
                warns.append(f"{code} has 'code also {req}' but {req} is absent — SCS-MULT-01")
        if c.get("morphology_required") and not any(codes.get(x, {}).get("type") == "morphology" for x in present):
            warns.append(f"{code} is a neoplasm needing a morphology code — SCS-MORPH-01")
        if c.get("dagger") and c.get("asterisk_pair") and c["asterisk_pair"] not in present:
            warns.append(f"dagger {code} present without its asterisk {c['asterisk_pair']} — SCS-DAG-01")
        for comp in c.get("supersedes", []):
            if comp in present:
                warns.append(f"combination {code} present with component {comp} — use the combination only (SCS-COMB-01)")

    for f in fails:
        print(f"FAIL  {f}")
    for w in warns:
        print(f"WARN  {w}")
    if not fails and not warns:
        print("OK  all validity edits passed")
    print(f"\n{len(fails)} fail(s), {len(warns)} warning(s).")
    sys.exit(1 if fails else 0)

# ---------- grouper (synthetic) ----------
def cmd_group(a):
    codes = load_codes()
    obj = _load(a.from_file)
    pdx = (obj.get("principal_diagnosis") or {}).get("code") or (_codes_in(obj) or [None])[0]
    pc = codes.get(pdx, {})
    mdc = pc.get("mdc", "00")
    base = BASE_DRG.get(pdx, "Z99")
    score = 0.0
    detail = []
    for d in obj.get("additional_diagnoses", []):
        c = codes.get(d.get("code"), {})
        w = SEV_WEIGHT.get(c.get("severity"), 0.5)
        if d.get("condition_onset_flag") == 2:
            w *= 1.5
        score += w
        detail.append(f"{d.get('code')}({c.get('severity')}x{'1.5' if d.get('condition_onset_flag')==2 else '1'})={w}")
    for p in obj.get("procedures", []):
        if codes.get(p.get("code"), {}).get("or_procedure"):
            score += 2.0
            detail.append(f"{p.get('code')}(OR proc)=2.0")
    level = "A" if score >= 4 else ("B" if score >= 2 else "C")
    print(json.dumps({
        "note": "SYNTHETIC mock grouper — not a licensed AR-DRG grouper.",
        "principal": pdx, "mdc": mdc, "base_drg": base,
        "complexity_score": round(score, 2), "complexity_detail": detail, "complexity_level": level,
        "predicted_ar_drg": {"code": f"S-DRG-{base}{level}", "description": f"(synthetic) MDC {mdc}, complexity {level}"}
    }, indent=2))

# ---------- verify grounding ----------
def cmd_verify(a):
    codes, rules = load_codes(), load_rules()
    obj = _load(a.from_file)
    items = _dx_items(obj) + [("procedure", p) for p in obj.get("procedures", [])]
    fails = 0
    for role, it in items:
        code = it.get("code")
        problems = []
        if code not in codes:
            problems.append("code not in code set (hallucination)")
        if not it.get("evidence_span"):
            problems.append("missing evidence_span")
        basis = it.get("scs_basis") or []
        if role != "procedure" and not basis:
            problems.append("missing scs_basis")
        for rid in basis:
            if rid not in rules:
                problems.append(f"unknown rule {rid}")
        status = "PASS" if not problems else "FAIL"
        if problems:
            fails += 1
        print(f"{status}  {role:11} {code}" + (f"  <- {'; '.join(problems)}" if problems else ""))
    print(f"\n{len(items)} code(s), {fails} failing.")
    sys.exit(1 if fails else 0)

# ---------- scoring ----------
def _f1(pred, gold):
    pred, gold = set(pred), set(gold)
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f

def _score(prop, gold, codes):
    pc, gc = _codes_in(prop), _codes_in(gold)
    p, r, f = _f1(pc, gc)
    principal_ok = (prop.get("principal_diagnosis", {}) or {}).get("code") == (gold.get("principal_diagnosis", {}) or {}).get("code")
    drg_ok = (prop.get("predicted_ar_drg", {}) or {}).get("code") == (gold.get("predicted_ar_drg", {}) or {}).get("code")
    hall = [c for c in pc if c not in codes]
    items = _dx_items(prop)
    grounded = sum(1 for _, it in items if it.get("evidence_span") and it.get("scs_basis"))
    # withholding: gold not_coded concepts that the proposal correctly did NOT emit
    nc = [n.get("candidate_code") for n in gold.get("not_coded", []) if n.get("candidate_code")]
    withheld = sum(1 for c in nc if c not in set(pc))
    return {"precision": round(p, 2), "recall": round(r, 2), "f1": round(f, 2),
            "principal_ok": principal_ok, "drg_ok": drg_ok, "hallucinations": len(hall),
            "grounded": f"{grounded}/{len(items)}", "withheld": f"{withheld}/{len(nc)}" if nc else "n/a"}

def cmd_check(a):
    codes = load_codes()
    m = _score(_load(a.proposal), _load(a.gold), codes)
    print("Coding eval (SYNTHETIC)")
    print(f"  precision/recall/F1 : {m['precision']} / {m['recall']} / {m['f1']}")
    print(f"  principal-dx match  : {'yes' if m['principal_ok'] else 'no'}")
    print(f"  AR-DRG match        : {'yes' if m['drg_ok'] else 'no'}")
    print(f"  hallucinated codes  : {m['hallucinations']}")
    print(f"  grounded dx         : {m['grounded']}")
    print(f"  withholding         : {m['withheld']}")

def cmd_eval(a):
    codes = load_codes()
    gold_dir = a.gold or os.path.join(EX, "gold")
    prop_dir = a.proposals or os.path.join(EX, "sample-proposals")
    rows = []
    for gp in sorted(glob.glob(os.path.join(gold_dir, "*.json"))):
        eid = os.path.splitext(os.path.basename(gp))[0]
        pp = os.path.join(prop_dir, eid + ".json")
        if not os.path.exists(pp):
            rows.append((eid, None))
            continue
        rows.append((eid, _score(_load(pp), _load(gp), codes)))
    print(f"Batch eval (SYNTHETIC)   proposals: {prop_dir}\n")
    print(f"{'episode':16} {'P':>4} {'R':>4} {'F1':>4}  {'pdx':>3} {'drg':>3} {'hall':>4} {'grounded':>9} {'withheld':>9}")
    scored = [m for _, m in rows if m]
    for eid, m in rows:
        if not m:
            print(f"{eid:16} {'— no proposal —'}")
            continue
        print(f"{eid:16} {m['precision']:>4} {m['recall']:>4} {m['f1']:>4}  "
              f"{'Y' if m['principal_ok'] else 'n':>3} {'Y' if m['drg_ok'] else 'n':>3} "
              f"{m['hallucinations']:>4} {m['grounded']:>9} {m['withheld']:>9}")
    if scored:
        n = len(scored)
        print(f"\nmacro F1={sum(m['f1'] for m in scored)/n:.2f}  "
              f"principal-dx acc={sum(m['principal_ok'] for m in scored)/n:.2f}  "
              f"DRG acc={sum(m['drg_ok'] for m in scored)/n:.2f}  "
              f"total hallucinations={sum(m['hallucinations'] for m in scored)}")

def cmd_example(a):
    epdir = os.path.join(EX, "episodes")
    files = sorted(os.listdir(epdir))
    if not a.id:
        print("Example episodes (assets/examples/episodes/):")
        for fn in files:
            print("  " + fn)
        print("\nGold codings in assets/examples/gold/. Pass an ID substring to print a note, e.g. `example EP-0001`.")
        return
    for fn in files:
        if a.id.lower() in fn.lower():
            print(open(os.path.join(epdir, fn)).read())
            return
    print(f"No example matching {a.id!r}", file=sys.stderr)
    sys.exit(1)

def main():
    ap = argparse.ArgumentParser(prog="ccagent.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog").set_defaults(fn=cmd_catalog)
    p = sub.add_parser("codes"); p.add_argument("query", nargs="?"); p.set_defaults(fn=cmd_codes)
    p = sub.add_parser("index"); p.add_argument("term", nargs="?"); p.set_defaults(fn=cmd_index)
    p = sub.add_parser("lookup"); p.add_argument("term", nargs="+"); p.set_defaults(fn=cmd_lookup)
    p = sub.add_parser("context"); p.add_argument("--from", dest="from_file", required=True); p.add_argument("--term"); p.set_defaults(fn=cmd_context)
    p = sub.add_parser("validate"); p.add_argument("code", nargs="+"); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("edits"); p.add_argument("--from", dest="from_file", required=True); p.set_defaults(fn=cmd_edits)
    p = sub.add_parser("group"); p.add_argument("--from", dest="from_file", required=True); p.set_defaults(fn=cmd_group)
    p = sub.add_parser("verify"); p.add_argument("--from", dest="from_file", required=True); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("check"); p.add_argument("--proposal", required=True); p.add_argument("--gold", required=True); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("eval"); p.add_argument("--proposals"); p.add_argument("--gold"); p.set_defaults(fn=cmd_eval)
    p = sub.add_parser("example"); p.add_argument("id", nargs="?"); p.set_defaults(fn=cmd_example)
    args = ap.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
