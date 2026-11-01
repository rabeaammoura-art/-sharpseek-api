# Project context for Claude (read this first in every session)

Owner: runs **3D ZONE TECH** (3D printing business, Jordan). Talk to them in **Arabic (Jordanian dialect)**, short and direct.
The repo is **public** — never commit purchase prices, the price sheet, product plans or personal data.

## What is here
- `worker.js`, `wrangler.toml`: the original "SharpSeek price search API" (Cloudflare worker). Unrelated to the 3D work.
- `cad/`: everything for the **newborn keepsake plaque** (bilingual Arabic/English, bear or baby, multi-colour, 4 filament slots).
  - `cad/newborn_plaque.py` — generator: `python cad/newborn_plaque.py cad/plaque/example_ar.json` -> 3MF (+ STL, PNG preview).
    JSON keys: `size` (any up to 290; 150/200/250/280 proven), `lang`, `name`, `weight`, `length`, `date`, `time`, `ampm`, `animal`
    (`bear`/`baby_boy`/`baby_girl`), `theme`, `stand` (`feet`/`rails`/`easel`/`clip`), `lit`, `glow`, `glow_cap`, `boxes`, `plate_x`, `layout` (`"train"` = engine + 4 wagon cards + bear + moon, theme `train`, ~285x190 at size 280, **the owner's chosen direction**; `"night"` = round version, rejected by the owner; both feet stand only).
  - `cad/print_files/` — ready files (see its README). `cad/plaque/gpt_prompt/` — prompts to get images from GPT.
  - `cad/STANDS.md` — all stand ideas, pros/cons, decisions. `cad/PRINTING_NOTES.md` — H2D/slicer findings. **Read both before changing stands or sizes.**
  - `cad/bambu_slice.py` (Linux only) slices with the Bambu Studio CLI and prices with the stock sheet; `/3d-cost*` skills use it.
  - Windows: `cad/README_WINDOWS.md` (`setup_windows.bat`, `make_plaque.bat`). Fonts are bundled in `cad/fonts`.
- `.claude/skills/3d-cost*`: time/cost estimates. They ask for the filament unless given.

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
