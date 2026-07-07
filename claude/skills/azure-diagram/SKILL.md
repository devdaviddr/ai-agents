---
name: azure-diagram
description: Create Azure cloud architecture diagrams as Excalidraw .excalidraw files, using a consistent Azure design system — category colour-coding, resource-group/VNet zone containers, service-node templates with official Azure icons, and flow arrows. Use when the user asks to draw, diagram, or visualise an Azure architecture, environment, resource group, network topology, or app/data/auth flow. Trigger on "/azure-diagram", "draw the Azure architecture", or "diagram this Azure setup".
allowed-tools: Read, Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/*)
---

# azure-diagram — Azure cloud diagrams in Excalidraw

Produce a clean Azure architecture diagram saved as a `.excalidraw` file the user can reopen and edit. The skill's job is **consistency**: every diagram uses the same Azure category colour-coding, zone containers, and node templates so they read as one family.

The generator is **bundled with this skill** and is pure-Python (stdlib only — no pip installs). Invoke it via the skill directory variable so it resolves at any install scope:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/azdiagram.py" catalog   # print the design-system catalog
python3 "${CLAUDE_SKILL_DIR}/scripts/azdiagram.py" icons     # list the bundled Azure icons
```

## Workflow

1. **Understand the architecture.** Identify the services, their groupings (resource group / Container Apps Environment / VNet), and the flows between them (data, auth, DNS). If the user pointed at an existing `.excalidraw` file or image, read it first and **match its existing colours and layout** rather than imposing new ones. Infer sensible defaults; only ask if the topology is genuinely ambiguous.

2. **Read the catalog.** Open `${CLAUDE_SKILL_DIR}/reference/azure-catalog.md` — the design system: category palette, zone styles, node recipe, arrow conventions, and the layout grid. Assign each service a category (Compute / Identity / Data / Storage / Networking / Integration / Monitoring) and pull its stroke + fill. `assets/templates/cae-bff-professional.json` is a canonical worked example of the target look.

3. **Compose the elements array.** Build a JSON array of Excalidraw elements following the catalog. Emit in z-order: **zones first** (back), then nodes, then labels, then arrows (front). Author each service node as a rounded rectangle with the `label` shorthand (centred bound text; first line the service name, then SKU/role) plus an `image` element carrying `"iconId": "<name>"` for its Azure icon. Honour the sizing rules: fontSize ≥14, nodes ≥120×60, 20–30px gaps, whole drawing ≤1200×900, no emoji. Keep the array in a temp file (e.g. `/tmp/els.json`) when large.

4. **Validate.** `python3 "${CLAUDE_SKILL_DIR}/scripts/azdiagram.py" validate --from /tmp/els.json` — flags missing required fields, duplicate ids, unknown types, and sub-14 font sizes.

5. **Save.**
   ```bash
   python3 "${CLAUDE_SKILL_DIR}/scripts/azdiagram.py" save "<out>.excalidraw" --from /tmp/els.json --professional
   ```
   **Always pass `--professional`** unless the user explicitly wants the sketchy look — it forces `roughness: 0` (clean lines) and `fontFamily: 2` (Helvetica, not the Virgil hand-drawn font), which is what makes it read as an Azure Architecture Center diagram. Default the output to `~/Desktop/<Name>-Architecture.excalidraw` unless the user gave a path; confirm before overwriting an existing file.

   **Two visual styles** — pick based on what the user wants:
   - *Pastel-box (default):* coloured category boxes on a white canvas (see the catalog's node recipe). Hand-author the elements array and `save --professional`.
   - *Dark / icon-centric* (the modern Microsoft-docs look — near-black canvas, the icon *is* the node, white captions, white elbow connectors): **use the `scene` builder** — don't hand-place coordinates. Describe a scene (nodes on a col/row grid + panels + edges) and the builder computes all geometry consistently, which is what makes this style work reliably across many diagrams:
     ```bash
     python3 "${CLAUDE_SKILL_DIR}/scripts/azdiagram.py" scene "<out>.excalidraw" --from /tmp/scene.json
     ```
     Dark + professional are on by default; edges accept an optional short `"label"`, and the builder prints a stderr `WARNING` for any edge it can't route cleanly (widen the grid if you see one). See the catalog's **"Dark / icon-centric theme → the `scene` builder"** section for the scene schema. Note: dark diagrams are white-on-dark, so open the saved file to view them (the MCP preview's white canvas would render white-on-white). To preview structure anyway, `scene --emit --from /tmp/scene.json` prints the elements JSON to pass to `create_view`.

6. **(Optional) Live render.** If an Excalidraw MCP is available in this session (e.g. a `create_view` / `export_to_excalidraw` tool), pass the same elements array to it to render the diagram inline and/or get a shareable excalidraw.com URL. If no such tool exists, skip this step silently — the `.excalidraw` file is the guaranteed deliverable.

## Key engine facts

- **Input:** a bare elements array *or* a `{"elements":[...]}` document. `save` expands each `label` into a real Excalidraw bound-text element, embeds each `iconId` as a base64 SVG in the file's `files` map, and **auto-groups** each node's box + icon + label so they drag together. `cameraUpdate`/`delete` pseudo-elements are stripped on save.
- **Icons:** `iconId` is an icon filename without `.svg` (see the `icons` command). Use an icon on **every** service node — it's what makes the diagram read as Azure.
- **Don't hand-write file text bindings.** Author nodes with the `label` shorthand; the script converts it. Writing `label` straight to a file would render an empty box.
- The `.excalidraw` wrapper (`type/version/source/elements/appState/files`) is written for you — you only ever author the `elements` array.
