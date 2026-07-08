#!/usr/bin/env python3
"""ccagent.py — deterministic helper for the clinical-coding skill (stdlib only).

Tools over a SYNTHETIC code set + coding standards. EVERYTHING HERE IS FICTIONAL:
the codes are a made-up Synthetic Clinical Classification (SCC) and the rules a made-up
Synthetic Coding Standards (SCS) — NOT ICD-10-AM/ACHI/ACS (copyright IHACPA), NOT medical
or coding advice. The model reasons; this script keeps codes real and grouping deterministic.

Subcommands:
  catalog                          summarise the code set + standards
  codes [QUERY]                    list/search codes
  lookup TERM...                   fuzzy-map a clinical term to candidate codes
  validate CODE...                 check codes exist (exit 1 if any don't)
  group  --from FILE               codes/proposal -> predicted (synthetic) AR-DRG
  verify --from PROPOSAL.json      check every code is real + grounded (evidence + rule)
  check  --proposal P --gold G     score a proposal against a gold coding
  example [ID]                     print an example episode note (default: list them)
"""
import sys, os, json, argparse, difflib

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(SKILL_DIR, "reference")
EX = os.path.join(SKILL_DIR, "assets", "examples")

# --- Synthetic mock grouper: principal code -> synthetic AR-DRG. NOT a real grouper. ---
DRG_MAP = {
    "DX-RESP-001": ("S-DRG-E65A", "COPD with catastrophic complication"),
    "DX-RESP-010": ("S-DRG-E62A", "Respiratory infection/inflammation"),
    "DX-CARD-001": ("S-DRG-F41A", "AMI with invasive cardiac intervention"),
    "DX-CARD-002": ("S-DRG-F74A", "Chest pain / angina"),
    "DX-ENDO-002": ("S-DRG-K60A", "Diabetes with catastrophic/severe complication"),
    "DX-ENDO-001": ("S-DRG-K60B", "Diabetes without catastrophic complication"),
    "DX-ENDO-003": ("S-DRG-K60A", "Diabetes with catastrophic/severe complication"),
}


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


def _codes_in(obj):
    """Pull the flat list of emitted codes from a proposal dict (or a bare list)."""
    if isinstance(obj, list):
        return [c if isinstance(c, str) else c.get("code") for c in obj]
    out = []
    if obj.get("principal_diagnosis"):
        out.append(obj["principal_diagnosis"].get("code"))
    for d in obj.get("additional_diagnoses", []):
        out.append(d.get("code"))
    for p in obj.get("procedures", []):
        out.append(p.get("code"))
    return [c for c in out if c]


def _load(path):
    with open(path) as f:
        return json.load(f)


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
            tags = ",".join(k for k in ("excludes", "code_also", "code_first") if instr.get(k))
            print(f"{code:14} {c['description']}" + (f"   [{tags}]" if tags else ""))


def cmd_lookup(a):
    codes = load_codes()
    term = " ".join(a.term).lower()
    scored = []
    for code, c in codes.items():
        score = difflib.SequenceMatcher(None, term, c["description"].lower()).ratio()
        if term in c["description"].lower():
            score += 0.4
        scored.append((round(score, 3), code, c["description"]))
    scored.sort(reverse=True)
    for score, code, desc in scored[:8]:
        print(f"{score:>5}  {code:14} {desc}")


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


def cmd_group(a):
    obj = _load(a.from_file)
    principal = obj["principal_diagnosis"]["code"] if isinstance(obj, dict) and obj.get("principal_diagnosis") else (_codes_in(obj) or [None])[0]
    drg, desc = DRG_MAP.get(principal, ("S-DRG-Z99Z", "Ungroupable / unspecified (synthetic fallback)"))
    print(json.dumps({"principal": principal, "predicted_ar_drg": {"code": drg, "description": f"(synthetic) {desc}"}}, indent=2))


def cmd_verify(a):
    codes = load_codes()
    rules = load_rules()
    obj = _load(a.from_file)
    items = []
    if obj.get("principal_diagnosis"):
        items.append(("principal", obj["principal_diagnosis"]))
    items += [("additional", d) for d in obj.get("additional_diagnoses", [])]
    items += [("procedure", p) for p in obj.get("procedures", [])]
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


def _f1(pred, gold):
    pred, gold = set(pred), set(gold)
    tp = len(pred & gold)
    p = tp / len(pred) if pred else 0.0
    r = tp / len(gold) if gold else 0.0
    f = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f


def cmd_check(a):
    codes = load_codes()
    prop, gold = _load(a.proposal), _load(a.gold)
    pc, gc = _codes_in(prop), _codes_in(gold)
    p, r, f = _f1(pc, gc)
    principal_ok = (prop.get("principal_diagnosis", {}).get("code") == gold.get("principal_diagnosis", {}).get("code"))
    drg_ok = (prop.get("predicted_ar_drg", {}).get("code") == gold.get("predicted_ar_drg", {}).get("code"))
    hallucinated = [c for c in pc if c not in codes]
    grounded = 0
    allitems = ([prop.get("principal_diagnosis")] if prop.get("principal_diagnosis") else []) + prop.get("additional_diagnoses", [])
    for it in allitems:
        if it and it.get("evidence_span") and it.get("scs_basis"):
            grounded += 1
    print("Coding eval (SYNTHETIC)")
    print(f"  precision/recall/F1 : {p:.2f} / {r:.2f} / {f:.2f}")
    print(f"  principal-dx match  : {'yes' if principal_ok else 'no'}")
    print(f"  AR-DRG match        : {'yes' if drg_ok else 'no'}")
    print(f"  hallucinated codes  : {len(hallucinated)}  {hallucinated if hallucinated else ''}")
    print(f"  grounded dx (span+rule): {grounded}/{len(allitems)}")


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
            with open(os.path.join(epdir, fn)) as f:
                print(f.read())
            return
    print(f"No example matching {a.id!r}", file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(prog="ccagent.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("catalog").set_defaults(fn=cmd_catalog)
    p = sub.add_parser("codes"); p.add_argument("query", nargs="?"); p.set_defaults(fn=cmd_codes)
    p = sub.add_parser("lookup"); p.add_argument("term", nargs="+"); p.set_defaults(fn=cmd_lookup)
    p = sub.add_parser("validate"); p.add_argument("code", nargs="+"); p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("group"); p.add_argument("--from", dest="from_file", required=True); p.set_defaults(fn=cmd_group)
    p = sub.add_parser("verify"); p.add_argument("--from", dest="from_file", required=True); p.set_defaults(fn=cmd_verify)
    p = sub.add_parser("check"); p.add_argument("--proposal", required=True); p.add_argument("--gold", required=True); p.set_defaults(fn=cmd_check)
    p = sub.add_parser("example"); p.add_argument("id", nargs="?"); p.set_defaults(fn=cmd_example)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
