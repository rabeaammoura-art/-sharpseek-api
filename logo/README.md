# Logo design pipeline

| Step | Tool | Output |
|---|---|---|
| Design | hand-written SVG in `src/` (or exported from Figma/Illustrator/Inkscape) | `src/<name>.svg` |
| Render | `rsvg-convert` (Pango text: Inter, Noto Sans Arabic) | `out/<name>.png`, `out/<name>@2x.png` |
| App icons | `rsvg-convert` + ImageMagick (only for `src/mark.svg`) | `out/icons/mark-{16..1024}.png`, `out/favicon.ico` |
| Review | ImageMagick `montage` | `out/preview.png` — every logo on light + dark, mark at 16–128 px |

## Usage

```bash
./logo/setup.sh     # once per fresh machine/session (the cloud SessionStart hook runs it)
cd logo
make                # build everything into out/
```

New logo or variant: drop `src/<name>.svg` and run `make`.
`src/mark.svg` is the square icon (favicon/app icon); `src/logo.svg` is the horizontal lockup.

Starter palette: blue `#2563eb` → violet `#7c3aed`, accent `#facc15`, muted `#64748b`, dark bg `#0b1220`.

Before shipping, convert text to outlines (Inkscape: *Path → Object to Path*) so the SVG
doesn't depend on installed fonts.
