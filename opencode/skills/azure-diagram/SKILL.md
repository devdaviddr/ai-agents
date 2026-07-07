---
name: azure-diagram
description: Create Azure cloud architecture diagrams as Excalidraw .excalidraw files, using a consistent Azure design system — category colour-coding, resource-group/VNet zone containers, service-node templates with official Azure icons, and flow arrows. Use when the user asks to draw, diagram, or visualise an Azure architecture, environment, resource group, network topology, or app/data/auth flow.
---

# azure-diagram — Azure cloud diagrams in Excalidraw

Produce a clean Azure architecture diagram saved as a `.excalidraw` file the user can open at [excalidraw.com](https://excalidraw.com) (File → Open) or with the VS Code Excalidraw extension. The skill's job is **consistency**: every diagram uses the same Azure category colour-coding, zone containers, and node templates so they read as one family.

## Locate the generator

The generator is **bundled with this skill** and is pure-Python (stdlib only — no pip installs). opencode has no skill-directory variable, so resolve the script among its known install locations, then reuse `$AZ`:

```bash
AZ=$(ls "$PWD"/.opencode/skills/azure-diagram/scripts/azdiagram.py \
        "$PWD"/.claude/skills/azure-diagram/scripts/azdiagram.py \
        "$PWD"/.agents/skills/azure-diagram/scripts/azdiagram.py \
        ~/.config/opencode/skills/azure-diagram/scripts/azdiagram.py \
        ~/.claude/skills/azure-diagram/scripts/azdiagram.py \
        ~/.agents/skills/azure-diagram/scripts/azdiagram.py 2>/dev/null | head -1)
python3 "$AZ" catalog   # print the design-system catalog
python3 "$AZ" icons     # list the bundled Azure icons
```

The script resolves its own icons and catalog relative to itself, so once `$AZ` is set everything works. (If `$AZ` is empty, the skill isn't installed where opencode is looking — fall back to `find ~ -path '*azure-diagram/scripts/azdiagram.py' 2>/dev/null | head -1`.)

## Workflow

1. **Understand the architecture.** Identify the services, their groupings (resource group / Container Apps Environment / VNet), and the flows between them (data, auth, DNS). If the user pointed at an existing `.excalidraw` file or image, read it first and **match its existing colours and layout**. Infer sensible defaults; only ask if the topology is genuinely ambiguous.

2. **Read the catalog.** The design system lives next to the script at `reference/azure-catalog.md` (i.e. `$(dirname "$AZ")/../reference/azure-catalog.md`) — category palette, zone styles, node recipe, arrow conventions, layout grid. Assign each service a category (Compute / Identity / Data / Storage / Networking / Integration / Monitoring) and pull its stroke + fill. `assets/templates/cae-bff-professional.json` is a canonical worked example.

3. **Compose the elements array.** Build a JSON array of Excalidraw elements following the catalog. Emit in z-order: **zones first** (back), then nodes, then labels, then arrows (front). Author each service node as a rounded rectangle with the `label` shorthand (centred bound text; first line the service name, then SKU/role) plus an `image` element carrying `"iconId": "<name>"` for its Azure icon. Honour the sizing rules: fontSize ≥14, nodes ≥120×60, 20–30px gaps, whole drawing ≤1200×900, no emoji. Keep the array in a temp file (e.g. `/tmp/els.json`).

4. **Validate.** `python3 "$AZ" validate --from /tmp/els.json` — flags missing required fields, duplicate ids, unknown types, and sub-14 font sizes.

5. **Save.**
   ```bash
   python3 "$AZ" save "<out>.excalidraw" --from /tmp/els.json --professional
   ```
   **Always pass `--professional`** unless the user explicitly wants the sketchy look — it forces `roughness: 0` (clean lines) and `fontFamily: 2` (Helvetica), which is what makes it read as an Azure Architecture Center diagram. Default the output to `~/Desktop/<Name>-Architecture.excalidraw` unless the user gave a path; confirm before overwriting.

   **Two visual styles** — pick based on what the user wants:
   - *Pastel-box (default):* coloured category boxes on a white canvas (see the catalog's node recipe). Hand-author the elements array and `save --professional`.
   - *Dark / icon-centric* (the modern Microsoft-docs look — near-black canvas, the icon *is* the node, white captions, white elbow connectors): **use the `scene` builder** — don't hand-place coordinates. Describe a scene (nodes on a col/row grid + panels + edges) and the builder computes all geometry consistently, which is what makes this style work reliably across many diagrams:
     ```bash
     python3 "$AZ" scene "<out>.excalidraw" --from /tmp/scene.json
     ```
     Dark + professional are on by default. See the catalog's **"Dark / icon-centric theme → the `scene` builder"** section for the scene schema.

6. **Open it.** opencode does not render Excalidraw inline, so tell the user to open the saved file at [excalidraw.com](https://excalidraw.com) (File → Open) or with the VS Code Excalidraw extension. (If you have configured an Excalidraw MCP you may also push the elements to it, but inline rendering isn't supported in the opencode UI.)

## Key engine facts

- **Input:** a bare elements array *or* a `{"elements":[...]}` document. `save` expands each `label` into a real Excalidraw bound-text element, embeds each `iconId` as a base64 SVG in the file's `files` map, and **auto-groups** each node's box + icon + label so they drag together.
- **Icons:** `iconId` is an icon filename without `.svg` (see the `icons` command). Use an icon on **every** service node.
- **Don't hand-write file text bindings.** Author nodes with the `label` shorthand; the script converts it. Writing `label` straight to a file would render an empty box.
- The `.excalidraw` wrapper (`type/version/source/elements/appState/files`) is written for you — you only ever author the `elements` array.
