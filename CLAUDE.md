# Project context for Claude (read this first in every session)

Owner: runs **3D ZONE TECH** (3D printing business, Jordan). Talk to them in **Arabic (Jordanian dialect)**, short and direct.
The repo is **public** — never commit purchase prices, the price sheet, product plans or personal data.

## What is here
- `worker.js`, `wrangler.toml`: the original "SharpSeek price search API" (Cloudflare worker). Unrelated to the 3D work.
- `cad/`: everything for the **newborn keepsake plaque** (bilingual Arabic/English, bear or baby, multi-colour, 4 filament slots).
  - `cad/newborn_plaque.py` — generator: `python cad/newborn_plaque.py cad/plaque/example_ar.json` -> 3MF (+ STL, PNG preview).
    JSON keys: `size` (any up to 290; 150/200/250/280 proven), `lang`, `name`, `weight`, `length`, `date`, `time`, `ampm`, `animal`
    (`bear`/`baby_boy`/`baby_girl`), `theme`, `stand` (`feet`/`rails`/`easel`/`clip`), `lit`, `glow`, `glow_cap`, `boxes`, `plate_x`, `layout` (`"train"` = engine + 4 wagon cards + bear + moon, theme `train`, ~285x190 at size 280, **the owner's chosen direction**; `"night"` = round version, rejected by the owner; both feet stand only); `"horse"` = rocking horse traced from a picture with `cad/trace_layers.py` (theme `horse`, stand still undecided)).
  - `cad/print_files/` — ready files (see its README). `cad/plaque/gpt_prompt/` — prompts to get images from GPT.
  - `cad/STANDS.md` — all stand ideas, pros/cons, decisions. `cad/PRINTING_NOTES.md` — H2D/slicer findings. **Read both before changing stands or sizes.**
  - `cad/bambu_slice.py` (Linux only) slices with the Bambu Studio CLI and prices with the stock sheet; `/3d-cost*` skills use it.
  - Windows: `cad/README_WINDOWS.md` (`setup_windows.bat`, `make_plaque.bat`). Fonts are bundled in `cad/fonts`.
- `.claude/skills/3d-cost*`: time/cost estimates. They ask for the filament unless given.

## Role: partner and development manager (agreed with the owner)
- In every session act as the owner's **partner and business-development manager**, not as a plain order-taker: lead, propose the plan and the next action, push back honestly, keep track of the timeline (printer arrival, products, pricing) yourself. Load the skill `anthropic-skills:3dzt-marketing-bd-manager` at the start of any 3D ZONE TECH conversation (it holds the marketing/pricing/channels rules).
- Bring ideas and execute the owner's ideas as shown; do not criticise or simplify them unprompted. One short line for a real blocker, then do the work.
- Print time is the owner's weak point: optimise time first, without asking. Keep answers short, plain Arabic, no tables unless asked.

## Current focus and rules (latest)
- Work on the **original plaque (name "يوسف", `cad/plaque/example_ar*.json`)**. The train / horse / night layouts are parked: do not bring them up unless the owner does.
- Backlit stand: closed box + folding leg. **The current `make_back_leg` hinge is WRONG** (screw through the back = leg swings in the plane of the back); the fix is a bracket with a horizontal hinge pin on the boss (M3 brass insert), pending owner approval. Plaque fixing in the box = planted hex nuts in the plaque back + screws from the back through posts (`fix_spec`, `fix_points`). Prefer **guaranteed** solutions (generous clearances, hardware screws), not print-in-place hinges/hooks. Show a perspective drawing and get a "yes" **before** editing files; if unsure what the owner means, **ask**, do not guess.

## Facts and preferences (decided with the owner)
- **The printer (Bambu Lab H2D) has not arrived yet.** Nothing is print-tested. Never say "print a test" as if they could; prepare files and software checks.
- Priorities: **print time matters more than cost**; no glue; no thicker base; avoid loose separate pieces; the owner likes things shown as images.
- Prices come only from `cad/config/filament_prices.xlsx` (git-ignored; ask the owner to upload `3D_ZONE_TECH_Filament.xlsx` if missing). PLA = PLA+.
- Plaque is printed front face up (relief on top, back on the bed). A 300 mm multi-colour plate + prime tower does not fit the H2D: **max coloured size is about 290 mm** (the generator warns above that; recommended ladder 150/200/250/280).
- Multi-colour estimates are only trustworthy **with** the prime tower (`--tower-x`). Single-colour estimates are reliable.
- Work directly on `main`, commit and push every change. Do not open PRs unless asked.
- **Shared memory between sessions:** a cloud session and a laptop session cannot see each other's chats. At the end of every task,
  append a short entry to `cad/WORKLOG.md` (date, cloud/laptop, what was done, what is left) and commit it. At the start of a
  session, read the top of `cad/WORKLOG.md`.

## Laptop / sessions
- The owner's laptop is **Windows**. Remote Control (cloud session working on the laptop) supports only Mac/Linux, so the laptop and the cloud sync **through GitHub** (pull/push).
- Claude Code installed locally on the laptop reads this same file, so it starts with the same context.
- The price sheet and any private file must be copied by hand to each machine.
- There is **no SessionStart hook** any more (it printed an error on the Windows laptop). In a **cloud (Linux) session** run `cad/setup.sh`
  yourself before using the Python/Bambu Studio tools (it installs `.venv-cad` and the Bambu Studio CLI; takes a few minutes).
