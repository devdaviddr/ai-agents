# Azure Excalidraw — Design System & Snippet Library

The visual language for ASG Azure architecture diagrams. Apply categories consistently:
every service of the same category gets the same stroke + fill, so a reader decodes the
diagram by colour. Print the live version any time with the bundled script (in this skill's
`scripts/` directory):

```bash
python3 "<skill-dir>/scripts/azdiagram.py" catalog   # Claude: <skill-dir> = ${CLAUDE_SKILL_DIR}
```

## Category palette

| Category | Stroke | Fill | Services |
|---|---|---|---|
| **Compute** | `#0078d4` | `#a5d8ff` | Container Apps, App Service, Functions, AKS, Container Instances, VM, VMSS |
| **Identity & Security** | `#8b5cf6` | `#d0bfff` | Entra ID, Managed Identity, Key Vault, Defender, RBAC, Entra B2C |
| **Data / Databases** | `#22c55e` | `#b2f2bb` | Azure SQL, Cosmos DB, PostgreSQL, MySQL, Redis, Synapse |
| **Storage** | `#06b6d4` | `#c3fae8` | Storage Account, Blob, Files, ADLS Gen2, Managed Disks |
| **Networking** | `#f59e0b` | `#ffd8a8` | Front Door, App Gateway/WAF, VNet, Subnet, Private Endpoint, DNS, Load Balancer, NSG |
| **Integration / Messaging** | `#ec4899` | `#eebefa` | Service Bus, Event Grid, Event Hubs, API Management, Logic Apps |
| **Monitoring / DevOps** | `#84cc16` | `#d8f5a2` | Log Analytics, App Insights, Azure Monitor, ACR, Azure DevOps, GitHub Actions |
| **Note / Warning** | `#f59e0b` | `#fff3bf` | Callouts, compliance warnings, captions |

These are conventions, not law — if the user's environment already standardised on a
colour (e.g. ACR drawn amber in an existing file), match the existing file instead.

## Zones (the containers a reader groups by)

A zone is a large rounded rectangle drawn **first** (so it sits behind its contents),
filled at low opacity, with a label pinned to its top-left corner as a separate text
element (not a centred `label`, which would float in the middle).

| Zone | Stroke | Fill | Opacity | strokeWidth |
|---|---|---|---|---|
| Resource Group | `#0078d4` | `#dbe4ff` | 18 | 2 |
| Container Apps Env / VNet | `#0078d4` | `#a5d8ff` | 18 | 3 (nested, thicker) |
| Logic / app tier | `#8b5cf6` | `#e5dbff` | 18 | 2 |
| Data tier | `#22c55e` | `#d3f9d8` | 18 | 2 |

```json
{"type":"rectangle","id":"rg","x":20,"y":80,"width":1160,"height":600,"roundness":{"type":3},"backgroundColor":"#dbe4ff","fillStyle":"solid","opacity":18,"strokeColor":"#0078d4","strokeWidth":2}
{"type":"text","id":"rg_lbl","x":42,"y":90,"width":280,"height":18,"text":"Resource Group   cqrc-test-rg","fontSize":14,"strokeColor":"#0078d4"}
```

## Node recipe (a service box)

Use a **labeled rounded rectangle** — the label auto-centres, no separate text element.
Default size 260×90; minimum 120×60. First line is the service, following lines are the
SKU / role / config.

```json
{"type":"rectangle","id":"bff","x":443,"y":276,"width":300,"height":120,"roundness":{"type":3},"backgroundColor":"#d0bfff","fillStyle":"solid","strokeColor":"#8b5cf6","strokeWidth":2,"label":{"text":"cqrc-bff\nHono.js BFF\nExternal Ingress","fontSize":16,"textAlign":"center","verticalAlign":"middle"}}
```

Common nodes (swap id/x/y):

- **Container App** — Compute colours, label `"<name>\n<runtime>\n<ingress>"`.
- **Entra ID** — Identity colours, label `"Microsoft Entra ID\n(Identity Provider)"`.
- **Managed Identity** — Identity colours, label `"User Assigned\nManaged Identity"`.
- **Azure SQL** — Data colours, label `"Azure SQL\n<db name>"`.
- **ACR** — Monitoring/DevOps colours, label `"Azure Container\nRegistry"`.
- **Log Analytics** — Monitoring colours, label `"Log Analytics\nWorkspace"`.
- **Front Door + WAF** — Networking colours, label `"Azure Front Door\n+ WAF"`.

## Professional (Azure Architecture Center) style

The default Excalidraw look (Virgil font + sketchy strokes) reads as a whiteboard doodle.
For a professional, Azure-Architecture-Center look, save with `--professional` (forces
`roughness:0` + `fontFamily:2`/Helvetica) and follow these patterns:

- **Node = rect + icon on top + label below, as SEPARATE standalone elements** (not a bound
  `label`). Icon 40×40 at top-centre (~14px below the top edge); name text directly under it
  (`textAlign:center`, text `x`=node.x, `width`=node.width to centre cleanly), tech/sub-label
  beneath. This keeps every text independently arrangeable and prevents icon/label overlap.
- **Clean palette** (lighter than the pastel fills): Compute `#0078D4`/`#E6F2FB`,
  Identity `#8B5CF6`/`#EDE7FB`, zone `#0078D4` dashed `#EAF3FB` @opacity 30. Text
  `#201F1E` (heading) / `#605E5C` (sub). Arrows `#5A6473` solid, `#8B5CF6` dashed for identity.
- **Numbered step badges**: a filled `ellipse` (22px) + a white `1`/`2`… on each flow, with a
  matching **legend box** mapping numbers → steps and solid/dashed line meaning.
- **Pill label backgrounds**: a small white rounded `rectangle` behind each arrow label so the
  text doesn't collide with the line.
- Title (fontSize 26) + subtitle (15) top-left; optional footer bottom-right. 20px grid.

`assets/templates/cae-bff-professional.json` is a worked example of all of the above.

## Dark / icon-centric theme (the Azure Architecture Center look)

Save with **`--dark`** for the modern Microsoft-docs aesthetic: a **near-black canvas**, the
**icon itself as the node** (no coloured box), **white captions**, and **white right-angled
(elbow) connectors**. `--dark` sets the dark background and turns near-black text/arrows white;
you supply the icon-centric layout. Use this when the user wants a clean, dark, icon-forward
diagram rather than the pastel-box house style.

**Icon node — a big icon with a white caption below it, no rectangle:**

```json
{"type":"image","id":"api_ic","iconId":"api-management","x":300,"y":900,"width":84,"height":84}
{"type":"text","id":"api_lbl","x":250,"y":996,"width":184,"height":40,"text":"Azure API\nManagement","fontSize":16,"textAlign":"center"}
```

- Icons **72–90px**. Centre the caption under the icon (`text.x = icon.x + icon.width/2 − text.width/2`), ~10px below it.
- **Group** each icon with its caption so they move together: add `"group":"n_api"` to both.
- Don't set text colour — `--dark` whitens it. (Or set `#ffffff` explicitly.)

**Elbow connectors — white, right-angled, bound to nodes:**

```json
{"type":"arrow","id":"a1","x":390,"y":940,"width":120,"height":0,"points":[[0,0],[120,0]],"elbowed":true,"endArrowhead":"arrow","startBinding":{"elementId":"web_ic","fixedPoint":[1,0.5]},"endBinding":{"elementId":"api_ic","fixedPoint":[0,0.5]}}
```

- `"elbowed":true` gives the orthogonal right-angle routing seen in Azure reference diagrams.
- Bind both ends to the **icon** elements so the elbows re-route cleanly when moved.
- Omit `strokeColor` (–dark makes it white) or set `#ffffff`.

**Panel container — the subtle grouping box (e.g. "CODEBASE STORAGE"):** dark fill, thin
bright-blue stroke, small blue label chip top-left. Draw it **first** so icons sit on top.

```json
{"type":"rectangle","id":"panel","x":1120,"y":150,"width":300,"height":760,"roundness":{"type":3},"backgroundColor":"#161b22","fillStyle":"solid","strokeColor":"#4c9aff","strokeWidth":2}
{"type":"text","id":"panel_lbl","x":1150,"y":170,"width":160,"height":40,"text":"CODEBASE\nSTORAGE","fontSize":14,"strokeColor":"#4c9aff"}
```

Title: white, fontSize 28–30, centred at top. Give rows ~120px vertical breathing room so
captions don't collide. Frame the whole drawing within ~2000×1200.

## Azure service icons

Official Microsoft Azure architecture icons are bundled in `assets/icons/` and embedded
into the saved `.excalidraw` file. List them:

```bash
python3 "<skill-dir>/scripts/azdiagram.py" icons
```

Add an icon by dropping an `image` element with an `iconId` (the icon filename without
`.svg`) — `azdiagram.py save` inlines the SVG as a base64 dataURL and wires up the
`files` map automatically. Place the icon at the **top-centre of its node**, then give the
node a `label` whose first line is blank-padded so text sits below the glyph (or shrink the
icon and offset the label). Recommended icon size 40–48px.

```json
{"type":"rectangle","id":"bff","x":480,"y":400,"width":270,"height":150,"roundness":{"type":3},"backgroundColor":"#a5d8ff","fillStyle":"solid","strokeColor":"#0078d4","strokeWidth":2,"label":{"text":"\nBFF — Express + Node.js\nContainer App","fontSize":18}}
{"type":"image","id":"bff_ic","iconId":"container-app","x":591,"y":410,"width":48,"height":48}
```

Note: embedded icons render in the saved **file** (excalidraw.com / VS Code extension).
The live MCP `create_view` preview may show them as placeholders — that's expected; the
file is the faithful artefact.

## Arrows (encode the kind of flow)

| Flow | strokeColor | strokeStyle | endArrowhead |
|---|---|---|---|
| Data / request | `#1e1e1e` | solid | arrow |
| Auth / OIDC / token | `#b0b0b0` | dashed | arrow |
| Category-tinted flow | category stroke | solid | arrow |

Label short (`"internal CAE DNS"`, `"HttpOnly cookie"`, `"OIDC code exchange"`); long
labels overflow short arrows — widen the arrow or shorten the text. Bind endpoints to
nodes so arrows stay attached:

```json
{"type":"arrow","id":"a1","x":300,"y":150,"width":150,"height":0,"points":[[0,0],[150,0]],"endArrowhead":"arrow","startBinding":{"elementId":"web","fixedPoint":[1,0.5]},"endBinding":{"elementId":"bff","fixedPoint":[0,0.5]}}
```

## Layout grid

- Title at `y≈10` (fontSize 28-30), subtitle below at `y≈52` (fontSize 18, category stroke).
- Resource Group zone starts `y≈80`. Top row of platform services (ACR, Log Analytics,
  Identity) inside it at `y≈110`. Nested env zone (CAE/VNet) below at `y≈232`.
- Service columns 333px wide with ~30px gaps; rows 340px tall for tall multi-line nodes.
- Keep the whole drawing inside ~1200×900 so it frames in an XL camera.

## Title block

```json
{"type":"text","id":"title","x":278,"y":10,"text":"CQRC — Test Environment","fontSize":30,"strokeColor":"#1e1e1e"}
{"type":"text","id":"subtitle","x":296,"y":52,"text":"Azure Container Apps  |  BFF Pattern","fontSize":18,"strokeColor":"#0078d4"}
```

## Warning / note callout (the yellow box pattern)

```json
{"type":"rectangle","id":"warn","x":40,"y":700,"width":760,"height":70,"roundness":{"type":3},"backgroundColor":"#fff3bf","fillStyle":"solid","strokeColor":"#f59e0b","strokeWidth":1,"opacity":60,"label":{"text":"No WAF — CAE managed ingress provides TLS + custom domain.\nAdd Azure Front Door + WAF if required for compliance.","fontSize":16,"textAlign":"left"}}
```
