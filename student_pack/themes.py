"""Theme definitions: palette, layer heights, name styling and the source-art crops that become motifs.

Crop boxes are pixel boxes (x0, y0, x1, y1) in art/source_art_osayd_sally.png.  `scale` is mm per source
pixel (the physical size the art was designed for: tag 70 mm, bottle 48 mm, pencil 85 mm, ruler 165 mm).
`seal` lists crop sides where the art is cut through (the name text starts there): an outline-coloured strip
is painted so the figure counts as closed, then clipped away again.
"""

ART = "art/source_art_osayd_sally.png"

THEMES = {
    "construction": dict(
        label="Construction (excavator + dump truck)",
        outline="black",
        letters="white",
        detail=None,                       # extra top colour (none: 4 colours = black, yellow, orange, white)
        # classification palette: name -> (rgb, colour it prints as)
        palette={
            "black": ((28, 28, 28), "black"), "yellow": ((246, 186, 28), "yellow"),
            "orange": ((250, 118, 20), "orange"), "white": ((252, 252, 252), "white"),
            "gray": ((150, 150, 150), "black"), "brown": ((140, 92, 45), "orange"),
            "lyellow": ((255, 215, 90), "yellow"),
        },
        filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C", "orange": "#FA7614", "white": "#FCFCFC"},
        heights={"black": 2.2, "yellow": 2.8, "orange": 2.8, "white": 3.2},
        # rings around the letters, from the letters outwards: (colour, width mm)
        text_rings=[("black", 0.8), ("yellow", 1.5), ("black", 1.5)],
        ruler=dict(band="black", ticks="white", rim="yellow", rim_w=1.6, stripes="yellow", body=None),
        motifs={
            "tag": dict(box=(20, 126, 392, 354), erase=[(106, 120, 244, 170)], bg="flood", seal=["bottom"], open=[(272, 262)],
                        scale=70 / 377, tab_x_px=175),
            "bottle": dict(box=(1205, 186, 1515, 378), paint=[("black", (1318, 160, 1405, 252))], bg="flood",
                           clip_circle=(1360, 330, 146), erase=[(1190, 100, 1536, 187)], seal=["bottom"], scale=48 / 310, tab_x_px=1360),
            "pencil_r": dict(box=(858, 36, 970, 207), bg="flood", seal=["left"], scale=85 / 457),
            "ruler_l": dict(box=(425, 318, 528, 444), bg="black", drop_edge=[("yellow", "bottom")], scale=165 / 785),
            "ruler_r": dict(box=(895, 316, 1142, 450), bg="black", drop_edge=[("yellow", "bottom"), ("white", "top"), ("orange", "top")], scale=165 / 785),
        },
    ),
    "cat": dict(
        label="Cat (original kitten)",
        outline="pink",
        letters="white",
        detail="black",
        palette={
            "pink": ((236, 48, 122), "pink"), "lpink": ((250, 168, 200), "lpink"),
            "white": ((252, 252, 252), "white"), "black": ((28, 28, 28), "black"),
            "mpink": ((253, 132, 175), "lpink"), "vlpink": ((255, 215, 230), "lpink"), "body": ((252, 190, 212), "lpink"),
            "pink2": ((253, 69, 131), "pink"), "heart": ((253, 93, 149), "pink"),
        },
        filament_rgb={"pink": "#EC307A", "lpink": "#FAA8C8", "white": "#FCFCFC", "black": "#1C1C1C"},
        heights={"pink": 2.2, "lpink": 2.8, "white": 3.2, "black": 3.4},
        text_rings=[("pink", 0.8), ("pink", 2.0)],
        ruler=dict(band="lpink", ticks="black", rim="pink", rim_w=1.6, stripes=None, body="lpink"),
        motifs={
            "tag": dict(box=(25, 590, 395, 850), paint=[("pink", (140, 480, 262, 652))], cut=[(140, 480, 262, 640)], bg="flood", seal=["bottom"],
                        scale=70 / 377, tab_x_px=205),
            "bottle": dict(box=(1215, 692, 1512, 872), erase=[(1190, 500, 1536, 692)], clip_circle=(1362, 840, 148),
                           paint=[("pink", (1318, 692, 1405, 728))], bg="flood", seal=["bottom"], scale=48 / 310,
                           tab_x_px=1362),
            "pencil_l": dict(box=(526, 566, 656, 724), bg="flood", seal=["right"], scale=85 / 533),  # mirrored for the right end
            "ruler_l": dict(box=(437, 808, 652, 972), bg="lpink", scale=165 / 785),
            "ruler_r": dict(box=(950, 834, 1176, 968), cut=[(950, 834, 974, 872)], bg="lpink", scale=165 / 785),
        },
    ),
}
