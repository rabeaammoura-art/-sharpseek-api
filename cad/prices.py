"""Filament prices from the 3D ZONE TECH stock sheet (landed JOD/kg, incl. shipping & customs).

The sheet lives at cad/config/filament_prices.xlsx and is NOT committed (the repo is public).
"""
from pathlib import Path

DEFAULT_FILE = Path(__file__).parent / "config" / "filament_prices.xlsx"


def load_prices(path=DEFAULT_FILE) -> dict:
    """{sheet type: landed price per kg} read from the Summary sheet."""
    import openpyxl
    if not Path(path).exists():
        raise SystemExit(f"Price sheet not found: {path}. Put 3D_ZONE_TECH_Filament.xlsx there "
                         "(or pass --price-kg).")
    ws = openpyxl.load_workbook(path, data_only=True)["Summary"]
    prices = {}
    for row in ws.iter_rows(min_row=3, values_only=True):
        if row[0] and isinstance(row[3], (int, float)) and row[0] != "TOTAL":
            prices[row[0]] = float(row[3])
    return prices


def sheet_type(profile_name: str) -> str:
    """Map a Bambu filament profile name to a type in the price sheet."""
    n = profile_name.lower()
    if "asa-cf" in n:
        return "ASA-CF"
    if "asa" in n:
        return "ASA"
    if "petg" in n:
        return "AD-PETG" if "translucent" in n else "PETG"
    if "silk" in n:
        return "Silk PLA"
    if "tpu" in n:
        return "TPU 95A"
    if "pla" in n:
        return "PLA+"   # Basic / Matte / Sparkle are priced as the PLA+ in stock
    raise SystemExit(f"No price mapping for '{profile_name}'. Add it to prices.sheet_type or pass --price-kg.")


def price_for(profile_name: str, prices: dict) -> tuple:
    t = sheet_type(profile_name)
    if t not in prices:
        raise SystemExit(f"'{t}' is not in the price sheet (have: {', '.join(prices)}).")
    return t, prices[t]
