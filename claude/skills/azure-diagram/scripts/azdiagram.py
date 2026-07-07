#!/usr/bin/env python3
"""azdiagram — wrap an Excalidraw elements array into a .excalidraw file, validate it,
or print the Azure service style catalog.

The same `elements` JSON you pass to the Excalidraw MCP `create_view` tool is the
input here. This tool exists so a live-rendered diagram can be persisted to disk as a
real .excalidraw file (openable in excalidraw.com, the VS Code Excalidraw extension,
Obsidian, etc.) without hand-writing the file wrapper.

Usage:
    azdiagram.py save  <out.excalidraw>  [--from elements.json]   # else reads stdin
    azdiagram.py validate                [--from elements.json]   # else reads stdin
    azdiagram.py catalog                                          # print style catalog

`elements` may be either a bare JSON array of elements, or a full Excalidraw document
(an object with an "elements" key) — both are accepted. cameraUpdate / delete /
restoreCheckpoint pseudo-elements are stripped on save (they are animation directives,
not drawable content) but tolerated on validate.
"""
import argparse
import base64
import hashlib
import json
import os
import sys

REQUIRED = ("type", "id", "x", "y", "width", "height")
PSEUDO = {"cameraUpdate", "delete", "restoreCheckpoint"}
DRAWABLE = {"rectangle", "ellipse", "diamond", "text", "arrow", "line", "freedraw", "image"}
CONTAINERS = {"rectangle", "ellipse", "diamond", "arrow"}
ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "icons")


def load(args):
    raw = open(args.from_file, encoding="utf-8").read() if args.from_file else sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"error: input is not valid JSON: {e}")
    if isinstance(data, dict) and "elements" in data:
        data = data["elements"]
    if not isinstance(data, list):
        sys.exit("error: expected a JSON array of elements (or a doc with an 'elements' array)")
    return data


def validate(elements):
    errors, ids = [], set()
    for i, el in enumerate(elements):
        if not isinstance(el, dict):
            errors.append(f"[{i}] not an object")
            continue
        t = el.get("type")
        if t in PSEUDO:
            continue
        if t not in DRAWABLE:
            errors.append(f"[{i}] unknown element type: {t!r}")
        # text auto-sizes from content; an icon-image gets width/height defaulted on save
        if t == "text" or (t == "image" and "iconId" in el):
            required = ("type", "id", "x", "y")
        else:
            required = REQUIRED
        for f in required:
            if f not in el:
                errors.append(f"[{i}] ({t}) missing required field: {f}")
        eid = el.get("id")
        if eid is not None:
            if eid in ids:
                errors.append(f"[{i}] duplicate id: {eid!r}")
            ids.add(eid)
        fs = el.get("fontSize")
        if isinstance(fs, (int, float)) and fs < 14:
            errors.append(f"[{i}] ({el.get('id')}) fontSize {fs} < 14 — unreadable at display scale")
    return errors


def _text_geometry(container, lines, font_size):
    """Approximate centred bound-text geometry. Excalidraw re-lays-out bound text on
    load, so these only need to be close enough to open cleanly."""
    cw = font_size * 0.55  # hand-drawn font avg char width
    text_w = max((len(ln) for ln in lines), default=1) * cw
    text_h = len(lines) * font_size * 1.25
    cx = container.get("x", 0) + container.get("width", 0) / 2
    cy = container.get("y", 0) + container.get("height", 0) / 2
    return round(cx - text_w / 2, 2), round(cy - text_h / 2, 2), round(text_w, 2), round(text_h, 2)


def expand_labels(elements):
    """Convert the MCP `label` shorthand into real Excalidraw bound-text elements.

    The live MCP renderer expands `label` itself, but a .excalidraw FILE needs a separate
    `text` element with `containerId` plus `boundElements` on the container — otherwise the
    shape opens EMPTY. This is the fix for that."""
    used = {e.get("id") for e in elements if isinstance(e, dict)}
    out = []
    for el in elements:
        if not isinstance(el, dict) or "label" not in el or el.get("type") not in CONTAINERS:
            out.append(el)
            continue
        lbl = el.pop("label")
        text = lbl.get("text", "")
        fs = lbl.get("fontSize", 16)
        tid = f"{el['id']}__t"
        i = 1
        while tid in used:
            tid = f"{el['id']}__t{i}"; i += 1
        used.add(tid)
        be = el.setdefault("boundElements", [])
        be.append({"type": "text", "id": tid})
        x, y, w, h = _text_geometry(el, text.split("\n"), fs)
        out.append(el)
        out.append({
            "type": "text", "id": tid, "x": x, "y": y, "width": w, "height": h,
            "text": text, "fontSize": fs, "fontFamily": lbl.get("fontFamily", 1),
            "textAlign": lbl.get("textAlign", "center"),
            "verticalAlign": lbl.get("verticalAlign", "middle"),
            "strokeColor": lbl.get("strokeColor", "#1e1e1e"),
            "containerId": el["id"],
        })
    return out


def embed_icons(elements, files):
    """Resolve `image` elements that carry an `iconId` into real embedded images,
    inlining the SVG from assets/icons/<iconId>.svg as a base64 dataURL."""
    missing = []
    for el in elements:
        if not isinstance(el, dict) or el.get("type") != "image" or "iconId" not in el:
            continue
        icon = el.pop("iconId")
        path = os.path.join(ICON_DIR, f"{icon}.svg")
        if not os.path.exists(path):
            missing.append(icon)
            continue
        fid = f"icon_{icon}"
        if fid not in files:
            with open(path, "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
            files[fid] = {
                "id": fid, "mimeType": "image/svg+xml",
                "dataURL": f"data:image/svg+xml;base64,{data}", "created": 0,
            }
        el["fileId"] = fid
        el.setdefault("width", 48)
        el.setdefault("height", 48)
    return missing


SHAPE_TYPES = {"rectangle", "ellipse", "diamond", "arrow", "line", "freedraw"}


def professionalize(elements):
    """Strip the hand-drawn look: clean (roughness 0) strokes on every shape/arrow and the
    Helvetica font (fontFamily 2) on every text + label. fontFamily map: 1=Virgil (hand-drawn),
    2=Helvetica (clean/professional), 3=Cascadia (code)."""
    for el in elements:
        if not isinstance(el, dict):
            continue
        t = el.get("type")
        if t in SHAPE_TYPES:
            el["roughness"] = 0
        if t == "text":
            el["fontFamily"] = 2
        if isinstance(el.get("label"), dict):
            el["label"]["fontFamily"] = 2


DARK_STROKES = {
    "", "#1e1e1e", "#1a1a1a", "#000000", "#000", "#201f1e", "#605e5c",
    "#343a40", "#495057", "#5a6473", "#212529",
}
DARK_BG = "#1a1a1a"
LIGHT_INK = "#ffffff"


def darkify(elements):
    """Recolor a diagram for a dark canvas (the icon-centric Azure look). Near-black text
    and arrow/line strokes become white so they read on the dark background; bright or grey
    colours (category strokes, #b0b0b0 auth arrows) are left as-is. Pairs with the icon-as-node
    recipe in the catalog (big icon + white caption, no filled box)."""
    for el in elements:
        if not isinstance(el, dict):
            continue
        t = el.get("type")
        sc = str(el.get("strokeColor", "")).lower()
        if t in ("text", "arrow", "line") and sc in DARK_STROKES:
            el["strokeColor"] = LIGHT_INK
        lbl = el.get("label")
        if isinstance(lbl, dict) and str(lbl.get("strokeColor", "")).lower() in DARK_STROKES:
            lbl["strokeColor"] = LIGHT_INK


def _gid(key):
    """Stable, deterministic Excalidraw groupId from a key — no RNG, so re-saves are stable."""
    return "grp" + hashlib.md5(key.encode("utf-8")).hexdigest()[:12]


def _norm_group(g):
    """A `group` value -> list of groupIds, innermost-first. Accepts a string or a list."""
    if isinstance(g, str):
        g = [g]
    if not isinstance(g, list):
        return []
    return [_gid(str(x)) for x in g]


def _center_inside(rect, el):
    """True if el's centre lies within rect's bounds."""
    ex = el.get("x", 0) + el.get("width", 0) / 2
    ey = el.get("y", 0) + el.get("height", 0) / 2
    rx, ry = rect.get("x", 0), rect.get("y", 0)
    return rx <= ex <= rx + rect.get("width", 0) and ry <= ey <= ry + rect.get("height", 0)


def apply_groups(elements, auto=True):
    """Assign Excalidraw `groupIds` so related elements select/drag as one unit.

    Explicit: any element with `"group": "name"` (or a list, innermost-first, for nesting)
    joins that named group; the same name -> the same group across elements.
    Auto (default): each icon `image` and bound-text label sitting inside a node rectangle is
    grouped WITH that rectangle, so a service node (box + icon + caption) moves as one piece —
    Excalidraw already drags bound text via containerId, but NOT the separate icon image, so
    this is the fix. Auto groups nest inside any explicit group on the node. The authoring-only
    `group` field is stripped. Returns the number of distinct groups formed."""
    explicit = {}  # element id -> [groupId, ...]
    for el in elements:
        if isinstance(el, dict) and "group" in el:
            explicit[el.get("id")] = _norm_group(el.pop("group"))

    auto_inner = {}   # element id -> innermost auto groupId
    inner_outer = {}  # inner groupId -> the node's explicit groups (so auto nests inside them)
    if auto:
        rects = [e for e in elements if isinstance(e, dict) and e.get("type") == "rectangle"]
        for el in elements:
            if not isinstance(el, dict):
                continue
            t, host = el.get("type"), None
            if t == "image" and "fileId" in el:  # an embedded icon -> smallest containing node
                holders = [r for r in rects if _center_inside(r, el)]
                if holders:
                    host = min(holders, key=lambda r: r.get("width", 0) * r.get("height", 0))
            elif t == "text" and el.get("containerId"):  # bound label -> its container node
                host = next((r for r in rects if r.get("id") == el["containerId"]), None)
            if host is not None and host is not el:
                inner = _gid("node:" + str(host.get("id")))
                auto_inner[el.get("id")] = inner
                auto_inner.setdefault(host.get("id"), inner)
                inner_outer[inner] = explicit.get(host.get("id"), [])

    groups = set()
    for el in elements:
        if not isinstance(el, dict):
            continue
        eid = el.get("id")
        if eid in auto_inner:  # node part: innermost auto group, then the node's explicit groups
            ids = [auto_inner[eid], *inner_outer.get(auto_inner[eid], [])]
        else:
            ids = list(explicit.get(eid, []))
        for g in (el.get("groupIds") or []):  # preserve any hand-authored groupIds
            if g not in ids:
                ids.append(g)
        if ids:
            el["groupIds"] = ids
            groups.update(ids)
    return len(groups)


def save(elements, out_path, professional=False, group=True, dark=False):
    drawable = [el for el in elements if isinstance(el, dict) and el.get("type") not in PSEUDO]
    if professional:
        professionalize(drawable)
    if dark:
        darkify(drawable)
    files = {}
    missing = embed_icons(drawable, files)
    drawable = expand_labels(drawable)
    ngroups = apply_groups(drawable, auto=group)
    app_state = {"gridSize": None, "viewBackgroundColor": DARK_BG if dark else "#ffffff"}
    if dark:
        app_state["theme"] = "dark"
    doc = {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": drawable,
        "appState": app_state,
        "files": files,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
    note = f"  [+{len(files)} embedded icons]" if files else ""
    gnote = f"  [{ngroups} groups]" if ngroups else ""
    print(f"wrote {out_path}  ({len(drawable)} elements){note}{gnote}")
    if missing:
        print(f"WARNING: icon(s) not found in assets/icons: {', '.join(sorted(set(missing)))}", file=sys.stderr)


CATALOG = """AZURE EXCALIDRAW STYLE CATALOG
Category coding — pick a category per service, use its stroke + fill consistently.

  Category               Stroke     Fill       Services
  ---------------------  ---------  ---------  --------------------------------------------
  Compute                #0078d4    #a5d8ff    Container Apps, App Service, Functions, AKS,
                                               Container Instances, VM, VMSS
  Identity & Security    #8b5cf6    #d0bfff    Entra ID, Managed Identity, Key Vault,
                                               Defender, RBAC, B2C
  Data / Databases       #22c55e    #b2f2bb    Azure SQL, Cosmos DB, PostgreSQL, MySQL,
                                               Redis Cache, Synapse
  Storage                #06b6d4    #c3fae8    Storage Account, Blob, Files, ADLS, Disks
  Networking             #f59e0b    #ffd8a8    Front Door, App Gateway/WAF, VNet, Subnet,
                                               Private Endpoint, DNS, Load Balancer, NSG
  Integration/Messaging  #ec4899    #eebefa    Service Bus, Event Grid, Event Hubs, APIM,
                                               Logic Apps, Functions (event-driven)
  Monitoring / DevOps    #84cc16    #d8f5a2    Log Analytics, App Insights, Monitor, ACR,
                                               Azure DevOps, GitHub Actions
  Note / Warning         #f59e0b    #fff3bf    Callout boxes, "no WAF" warnings, captions

Zone / container backgrounds (big rounded rect behind a group, opacity 15-20):
  Resource Group   stroke #0078d4  fill #dbe4ff   label top-left "Resource Group  <name>"
  CAE / VNet / Env stroke #0078d4  fill #a5d8ff   nested inside the RG, strokeWidth 3
  Logic zone       stroke #8b5cf6  fill #e5dbff
  Data zone        stroke #22c55e  fill #d3f9d8

Node recipe (a service box):
  {"type":"rectangle","id":"<id>","x":..,"y":..,"width":260,"height":90,
   "roundness":{"type":3},"backgroundColor":"<fill>","fillStyle":"solid",
   "strokeColor":"<stroke>","strokeWidth":2,
   "label":{"text":"<Service>\\n<detail>","fontSize":16,"textAlign":"center","verticalAlign":"middle"}}

Conventions: fontSize >=16 body / >=20 titles; node min 120x60, prefer 260x90;
20-30px gaps; dashed grey arrows (#b0b0b0) for auth/OIDC, solid black for data flow,
category-stroke arrows to colour-code a flow. No emoji (won't render).

DARK / ICON-CENTRIC THEME  (save with --dark)  -- the Azure Architecture Center look:
  Instead of a coloured box per service, the ICON *is* the node. Dark canvas, white text,
  white elbow (right-angled) connectors. This is what --dark + this recipe produce.

  1. Icon node = a big icon image + a white caption below it, NO rectangle:
     {"type":"image","id":"api_ic","iconId":"api-management","x":..,"y":..,"width":84,"height":84}
     {"type":"text","id":"api_lbl","x":<icon.x+42-w/2>,"y":<icon.y+92>,"text":"Azure API\\nManagement",
      "fontSize":16,"textAlign":"center"}     # --dark turns dark text white for you
     Group each icon with its caption:  add "group":"n_api" to both.
  2. Elbow connectors: white, right-angled. Add "elbowed":true and bind both ends:
     {"type":"arrow","id":"a1","x":..,"y":..,"width":..,"height":..,"points":[[0,0],[dx,0],[dx,dy]],
      "elbowed":true,"strokeColor":"#ffffff","endArrowhead":"arrow",
      "startBinding":{"elementId":"web","fixedPoint":[1,0.5]},"endBinding":{"elementId":"api","fixedPoint":[0,0.5]}}
     (--dark also recolours any near-black arrow to white, so you can omit strokeColor.)
  3. Panel container (the subtle "CODEBASE STORAGE" box): dark fill, thin bright-blue stroke,
     small label chip top-left. Draw it FIRST so icons sit on top:
     {"type":"rectangle","id":"panel","x":..,"y":..,"width":..,"height":..,"roundness":{"type":3},
      "backgroundColor":"#161b22","fillStyle":"solid","strokeColor":"#4c9aff","strokeWidth":2}
     {"type":"text","id":"panel_lbl","x":..,"y":..,"text":"CODEBASE\\nSTORAGE","fontSize":14,"strokeColor":"#4c9aff"}
  4. Title: white, fontSize 28-30, centred at top. Icons 72-90px; ~120px vertical gap between
     an icon and the next row so captions don't collide. Keep everything inside ~2000x1200."""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("save", "validate"):
        sp = sub.add_parser(name)
        sp.add_argument("out", nargs="?" if name == "validate" else None)
        sp.add_argument("--from", dest="from_file", help="read elements JSON from this file (else stdin)")
        if name == "save":
            sp.add_argument("--professional", action="store_true",
                            help="clean look: roughness 0 on shapes, Helvetica (fontFamily 2) on text")
            sp.add_argument("--dark", action="store_true",
                            help="dark canvas: near-black background + white text/arrows (pairs with the icon-centric recipe)")
            sp.add_argument("--no-auto-group", dest="auto_group", action="store_false",
                            help="disable auto-grouping a node's box+icon+label (explicit `group` still applies)")
    sub.add_parser("catalog")
    sub.add_parser("icons")
    args = p.parse_args()

    if args.cmd == "catalog":
        print(CATALOG)
        return
    if args.cmd == "icons":
        if not os.path.isdir(ICON_DIR):
            sys.exit("no icons installed yet (assets/icons is missing)")
        names = sorted(f[:-4] for f in os.listdir(ICON_DIR) if f.endswith(".svg"))
        print(f"{len(names)} Azure icons available (use as iconId on an image element):")
        for n in names:
            print("  " + n)
        return

    elements = load(args)
    errors = validate(elements)
    if errors:
        print("VALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        sys.exit(1)
    if args.cmd == "validate":
        print(f"OK — {len([e for e in elements if e.get('type') not in PSEUDO])} drawable elements, no errors")
    else:
        save(elements, args.out, professional=getattr(args, "professional", False),
             group=getattr(args, "auto_group", True), dark=getattr(args, "dark", False))


if __name__ == "__main__":
    main()
