"""v4 base / cable modifications: sealed back, wide channel to the base, open-bottom trench to the rear edge."""
import numpy as np
import trimesh
import teddy_edit as te
from heart import X0

CH_Y = 847.0            # channel centre (y)
CH_R = 6.0              # channel radius (diameter 12)
TRENCH_W, TRENCH_H = 12.0, 5.0


def back_and_cable(teddy):
    plug, resid = te._back_plug(teddy)
    t = te.boolean("union", [teddy, plug])
    t = te.retriangulate_back_patch(t)
    # dead-end of the old slot (behind the channel) is filled
    fill = trimesh.creation.box(bounds=[[X0 - 4.6, CH_Y + CH_R - 0.6, 52.4], [X0 + 4.6, 873.0, 63.4]])
    t = te.boolean("union", [t, fill])
    chan = trimesh.creation.cylinder(radius=CH_R, height=62.0, sections=96,
                                     transform=trimesh.transformations.translation_matrix([X0, CH_Y, 29.0]))
    trench = trimesh.creation.box(bounds=[[X0 - TRENCH_W / 2, CH_Y, -1.0], [X0 + TRENCH_W / 2, 925.0, TRENCH_H]])
    return te.boolean("difference", [t, chan, trench])
