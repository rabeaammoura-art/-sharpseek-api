"""PLA+ colours in stock (3D_ZONE_TECH_Filament.xlsx) with the hex used for previews and AMS slot colours.
Keep in sync with STOCK in website/site.src.html."""
PLA_PLUS = {"white": "#F2F2F2", "black": "#1C1C1C", "red": "#D32F2F", "blue": "#1E5BD8", "yellow": "#F6BA1C", "green": "#2E9E4F",
            "orange": "#FA7614", "purple": "#7B3FA0", "pink": "#EC407A", "cyan": "#14B8D4", "grey": "#8E9196"}


def _lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    x, y = _lum(a), _lum(b)
    return (max(x, y) + 0.05) / (min(x, y) + 0.05)


def parse_palette(spec):
    """'black=blue,yellow=white' -> {'black': '#1E5BD8', 'yellow': '#F2F2F2'}  (stock colour names or #RRGGBB)."""
    out = {}
    for part in spec.split(","):
        role, _, val = part.partition("=")
        role, val = role.strip().lower(), val.strip()
        h = val if val.startswith("#") and len(val) == 7 else PLA_PLUS.get(val.lower())
        if not role or h is None:
            raise ValueError(f"bad palette entry {part!r}: use ROLE=COLOUR with a stock colour ({', '.join(PLA_PLUS)}) or #RRGGBB")
        out[role] = h.upper()
    return out
