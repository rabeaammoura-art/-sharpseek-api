"""Front-view drawing of retrofit face plates (section through the plate), side by side.

Usage: python drawing.py out/compare.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from build123d import Plane, section

sys.path.insert(0, str(Path(__file__).parent / "parts"))
import retrofit_housing as rh  # noqa: E402

VARIANTS = [
    ('1 x 5.75" (146 mm)', rh.SINGLE_575, rh.TOP_WINDOW, rh.BOTTOM_WINDOW),
    ('2 x 4.5" (114 mm)', rh.TWIN_45, (0, 0, 0), (0, 0, 0)),
]


def plot_section(ax, part, y, **style):
    for e in section(part, Plane((0, y, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))).edges():
        pts = [e.position_at(t / 60) for t in range(61)]
        ax.plot([p.X for p in pts], [p.Z for p in pts], **style)


fig, axs = plt.subplots(1, len(VARIANTS), figsize=(11, 8))
shell = rh.shell()
for ax, (title, lights, top, bottom) in zip(axs, VARIANTS):
    plot_section(ax, shell, -rh.FACE_T - 30, color="0.6", lw=1, ls="--")
    plot_section(ax, rh.face_plate(lights, top, bottom), -rh.FACE_T / 2, color="k", lw=1.2)
    for (d, z), gap in zip(lights, rh.clearances(lights)):
        r = (d + rh.LIGHT_CLEARANCE) / 2
        ax.annotate("", (-r, z), (r, z), arrowprops=dict(arrowstyle="<->", color="tab:blue"))
        ax.text(0, z + 3, f"Ø{d}", ha="center", color="tab:blue")
        ax.text(r + 1, z - 12, f"min {gap:.1f} mm\nto inner wall", fontsize=7, color="tab:red")
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.grid(alpha=0.3)
    ax.set_xlabel("width X (mm)")
    ax.set_ylabel("height Z (mm)")
fig.suptitle("Face plate — front view (dashed = shell wall)")
plt.tight_layout()
out = sys.argv[1] if len(sys.argv) > 1 else "out/retrofit_compare.png"
plt.savefig(out, dpi=110)
print(out)
