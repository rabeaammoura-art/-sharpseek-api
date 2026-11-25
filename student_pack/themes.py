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
                        scale=70 / 377, tab_x_px=175, heal=[("yellow", 0.45)], absorb=[("orange", 25.0, "yellow"), ("black", 2.0, "yellow")]),
            "bottle": dict(box=(1205, 186, 1515, 378), paint=[("black", (1318, 160, 1405, 252))], bg="flood",
                           clip_circle=(1360, 330, 146), erase=[(1190, 100, 1536, 187)], seal=["bottom"], scale=48 / 310, tab_x_px=1360),
            "pencil_r": dict(box=(858, 36, 970, 207), bg="flood", seal=["left"], scale=85 / 457),
            "ruler_l": dict(box=(425, 318, 528, 444), bg="black", drop_edge=[("yellow", "bottom")], scale=165 / 785),
            "ruler_r": dict(box=(895, 316, 1142, 450), bg="black", drop_edge=[("yellow", "bottom"), ("white", "top"), ("orange", "top"), ("yellow", "left"), ("orange", "left"), ("yellow", "right"), ("orange", "right")], scale=165 / 785,
                            erase=[(895, 432, 918, 450), (1008, 437, 1050, 450), (1124, 427, 1142, 450)],   # stripes of the neighbouring art
                            paint_poly=[("yellow", [(992, 341), (1015, 336), (1137, 360), (1138, 366), (1137, 389), (1102, 394), (1052, 413), (1012, 413)])],  # dump bed: no ribs
                            heal=[("yellow", 0.45)], absorb=[("orange", 12.0, "yellow")]),
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
            "tag": dict(box=(25, 590, 395, 850), erase_poly=[[(100, 560), (290, 560), (290, 590), (268, 618), (258, 624), (245, 638), (205, 641), (165, 638), (150, 624), (125, 604), (100, 590)]], bg="flood", seal=["bottom"],
                        scale=70 / 377, tab_x_px=205),
            "bottle": dict(box=(1215, 692, 1512, 872), erase=[(1190, 500, 1536, 692)], clip_circle=(1362, 840, 148),
                           paint=[("pink", (1318, 692, 1405, 728))], bg="flood", seal=["bottom"], scale=48 / 310,
                           tab_x_px=1362),
            "pencil_l": dict(box=(526, 566, 656, 724), bg="flood", seal=["right"], scale=85 / 533),  # mirrored for the right end
            "ruler_l": dict(box=(437, 808, 652, 972), bg="lpink", scale=165 / 785),
            "ruler_r": dict(box=(950, 834, 1176, 968), cut=[(950, 834, 974, 872)], bg="lpink", scale=165 / 785),
        },
    ),

    "cars": dict(
        label="Cars (sport car + chequered flags), same colours as Construction",
        art="art/source_art_cars.png",
        outline="black",
        letters="white",
        detail=None,
        palette={
            "black": ((20, 20, 20), "black"), "yellow": ((255, 232, 0), "yellow"),
            "orange": ((255, 126, 0), "orange"), "white": ((255, 255, 255), "white"),
            "gray": ((150, 150, 150), "black"), "brown": ((140, 92, 45), "orange"),
            "lyellow": ((255, 215, 90), "yellow"),
        },
        filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C", "orange": "#FA7614", "white": "#FCFCFC"},
        heights={"black": 2.2, "yellow": 2.8, "orange": 2.8, "white": 3.2},
        text_rings=[("black", 0.8), ("yellow", 1.5), ("black", 1.5)],
        ruler=dict(band="black", ticks="white", rim="yellow", rim_w=1.6, stripes="yellow", body=None),
        motifs={
            "tag": dict(box=(80, 118, 718, 396), erase=[(80, 368, 142, 396), (645, 372, 718, 396)], bg="flood", seal=["bottom"],
                        scale=70 / 638, tab_x_px=370, heal=[("orange", 0.3)]),
            "bottle": dict(box=(1100, 628, 1445, 796), bg="flood", seal=["bottom"], scale=48 / 345, tab_x_px=1272,
                           erase_poly=[[(1096, 624), (1180, 624), (1096, 705)], [(1450, 624), (1366, 624), (1450, 700)]]),   # ring arcs of the round tag
            "pencil_r": dict(box=(1228, 272, 1484, 386), bg="black", scale=85 / 780),
            "ruler_l": dict(box=(46, 770, 298, 890), bg="black", scale=165 / 1020),
            "ruler_r": dict(box=(778, 768, 1006, 892), bg="black", scale=165 / 1020),
        },
    ),
    "gamer": dict(
        label="Gamer boy (private: made for Osayd), 4 colours",
        private=True,
        sil_open=1.0,                              # trim outline spurs thinner than 2 mm                              # not sold: stays out of the price catalog and the website
        art="art/source_art_gamer.png",
        outline="black",
        letters="white",
        detail=None,
        palette={
            "black": ((2, 2, 2), "black"), "dark": ((60, 44, 47), "black"),
            "white": ((253, 253, 253), "white"), "grey": ((127, 125, 125), "white"), "lgrey": ((200, 193, 194), "white"),
            "red": ((250, 8, 9), "red"),
            "blue": ((2, 169, 250), "blue"), "dblue": ((1, 92, 142), "blue"),
        },
        filament_rgb={"black": "#1C1C1C", "blue": "#1E5BD8", "red": "#D32F2F", "white": "#F2F2F2"},
        heights={"black": 2.2, "blue": 2.8, "red": 2.8, "white": 3.2},
        text_rings=[("black", 0.8), ("blue", 1.5), ("black", 1.5)],
        ruler=dict(band="black", ticks="white", rim="blue", rim_w=1.6, stripes=None, body=None),
        motifs={
            "tag": dict(box=(0, 130, 600, 548), bg="flood", seal=["bottom"], scale=70 / 600, tab_x_px=310),
            "bottle": dict(box=(805, 718, 1250, 985), bg="flood", seal=["bottom"], clip_circle=(1028, 948, 222), scale=48 / 445, tab_x_px=1028),
            "pencil_l": dict(box=(648, 368, 764, 490), bg="black", erase=[(648, 468, 674, 490), (744, 478, 764, 490)], scale=85 / 650),
            "pencil_r": dict(box=(1040, 372, 1212, 505), bg="black", erase=[(1122, 364, 1180, 390)], scale=85 / 650),
            "ruler_l": dict(box=(28, 897, 190, 1132), bg="black", scale=165 / 800),
            "ruler_r": dict(box=(662, 898, 792, 1132), bg="black", scale=165 / 800),
        },
    ),
    "gamer_girl": dict(
        label="Gamer girl (private: made for Saly), 4 colours",
        private=True,
        fill_counters=True,
        sil_open=1.0,                              # trim outline spurs thinner than 2 mm
        tab_under_art=True,                        # the bow stays visible under the hanging loop
        art="art/source_art_gamer_saly.png",
        outline="yellow",
        letters="white",
        detail=None,
        palette={
            "white": ((253, 252, 252), "white"), "lpink": ((215, 167, 206), "white"),
            "yellow": ((252, 199, 3), "yellow"), "lyellow": ((252, 226, 123), "yellow"), "brown": ((173, 106, 41), "yellow"),
            "purple": ((106, 8, 121), "purple"), "dpurple": ((77, 6, 96), "purple"), "maroon": ((68, 10, 52), "purple"), "mpurple": ((149, 92, 154), "purple"),
            "pink": ((240, 4, 123), "pink"),
        },
        filament_rgb={"yellow": "#F6BA1C", "purple": "#7B3FA0", "pink": "#EC407A", "white": "#F2F2F2"},
        heights={"yellow": 2.2, "purple": 2.8, "pink": 2.8, "white": 3.2},
        text_rings=[("purple", 3.0), ("yellow", 1.5)],
        ruler=dict(band="purple", ticks="white", rim="yellow", rim_w=1.6, stripes=None, body="purple"),
        motifs={
            "tag": dict(box=(20, 134, 612, 562), erase=[(600, 134, 612, 562)], bg="flood", seal=["bottom"], scale=70 / 592, tab_x_px=305,
                        thin=[("yellow", 0.7, "white", (260, 300, 560, 520))],
                        absorb=[("yellow", 1.2, "purple", (260, 300, 560, 520))]),   # thin yellow slivers along the face / hand outlines
            "bottle": dict(box=(788, 716, 1252, 992), bg="flood", seal=["bottom"], clip_circle=(1020, 952, 232), scale=48 / 464, tab_x_px=1020,
                           thin=[("yellow", 0.7, "white", (880, 790, 1160, 975))],
                           absorb=[("yellow", 1.0, "purple", (880, 790, 1160, 975))]),   # ends at the chin: no hoodie scraps
            "pencil_l": dict(box=(632, 366, 764, 498), bg="purple", scale=85 / 660),
            "pencil_r": dict(box=(1040, 392, 1224, 508), bg="purple", scale=85 / 660),
            "ruler_l": dict(box=(24, 918, 176, 1138), bg="purple", scale=165 / 800),
            "ruler_r": dict(box=(660, 918, 785, 1138), bg="purple", scale=165 / 800),
        },
    ),
}


def _derive(base, name, label, remap, **over):
    """Fewer-colour variant of a traced theme: motif layers are merged by `remap` (e.g. white -> black) and the
    layer stack / name styling / ruler layout are overridden.  Same art, fewer filament changes."""
    d = dict(THEMES[base], label=label, variant_of=base, remap=remap)
    d.update(over)
    THEMES[name] = d


_derive("construction", "construction3", "Construction, 3 colours (black, yellow, orange)", {"white": "black"},
        letters="yellow", filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C", "orange": "#FA7614"},
        heights={"black": 2.2, "yellow": 2.8, "orange": 2.8}, text_rings=[("black", 2.2)],
        ruler=dict(band="yellow", ticks="black", rim="black", rim_w=1.6, stripes="black", body="yellow", halo=1.2))
_derive("construction", "construction2", "Construction, 2 colours (black, yellow)", {"white": "black", "orange": "yellow"},
        letters="yellow", filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C"},
        heights={"black": 2.2, "yellow": 2.8}, text_rings=[("black", 2.2)],
        ruler=dict(band="yellow", ticks="black", rim="black", rim_w=1.6, stripes="black", body="yellow", halo=1.2))

_cat_ruler = dict(band="pink", ticks="white", rim="pink", rim_w=1.6, stripes=None, body=None)
_derive("cars", "cars3", "Cars, 3 colours (black, yellow, orange)", {"white": "yellow"},
        letters="yellow", filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C", "orange": "#FA7614"},
        heights={"black": 2.2, "yellow": 2.8, "orange": 2.8}, text_rings=[("black", 2.2)],
        ruler=dict(band="yellow", ticks="black", rim="black", rim_w=1.6, stripes="black", body="yellow", halo=1.2))
_derive("cars", "cars2", "Cars, 2 colours (black, yellow)", {"white": "yellow", "orange": "yellow"},
        letters="yellow", filament_rgb={"black": "#1C1C1C", "yellow": "#F6BA1C"},
        heights={"black": 2.2, "yellow": 2.8}, text_rings=[("black", 2.2)],
        ruler=dict(band="yellow", ticks="black", rim="black", rim_w=1.6, stripes="black", body="yellow", halo=1.2))
_derive("cat", "cat3", "Cat, 3 colours (pink, white, black)", {"lpink": "pink"},
        filament_rgb={"pink": "#EC307A", "white": "#FCFCFC", "black": "#1C1C1C"},
        heights={"pink": 2.2, "white": 3.2, "black": 3.4}, ruler=_cat_ruler)
_derive("cat", "cat2", "Cat, 2 colours (pink, white)", {"lpink": "pink", "black": "pink"},
        filament_rgb={"pink": "#EC307A", "white": "#FCFCFC"}, detail=None,
        heights={"pink": 2.2, "white": 3.2}, ruler=_cat_ruler)

# 3-colour versions of the private gamer themes (art untouched, one colour merged into a neighbour: chosen by comparing renders)
_derive("gamer", "gamer3", "Gamer boy (private), 3 colours: blue merged into red", {"blue": "red"},
        filament_rgb={"black": "#1C1C1C", "red": "#D32F2F", "white": "#F2F2F2"}, heights={"black": 2.2, "red": 2.8, "white": 3.2},
        text_rings=[("black", 0.8), ("red", 1.5), ("black", 1.5)], ruler=dict(THEMES["gamer"]["ruler"], rim="red"))
THEMES["gamer_girl3"] = dict(
    label="Gamer girl (private: made for Sally), 3 colours, redrawn by GPT for 3 flat colours",
    private=True,
    art="art/source_art_gamer_saly3.png",
    outline="yellow",
    letters="white",
    detail=None,
    fill_counters=True,
    sil_open=1.0,
    tab_under_art=True,
    palette={"yellow": ((253, 192, 15), "yellow"), "pink": ((230, 30, 110), "pink"), "white": ((254, 254, 254), "white")},
    filament_rgb={"yellow": "#F6BA1C", "pink": "#EC407A", "white": "#F2F2F2"},
    heights={"yellow": 2.2, "pink": 2.8, "white": 3.2},
    text_rings=[("pink", 3.0), ("yellow", 1.5)],
    ruler=dict(band="pink", ticks="white", rim="yellow", rim_w=1.6, stripes=None, body="pink"),
    motifs={
        "tag": dict(box=(12, 116, 490, 468), bg="flood", seal=["bottom"], scale=70 / 465, tab_x_px=255),
        "bottle": dict(box=(535, 116, 858, 306), bg="flood", seal=["bottom"], scale=48 / 312, tab_x_px=692),
        "pencil_l": dict(box=(24, 702, 138, 826), bg="flood", scale=0.143),
        "pencil_r": dict(box=(460, 722, 620, 815), bg="flood", scale=0.143),
        "ruler_l": dict(box=(62, 998, 265, 1215), bg="pink", scale=0.1422),
        "ruler_r": dict(box=(992, 1000, 1168, 1215), bg="pink", scale=0.1422),
    },
)

# Sally, 4 colours, redrawn/cleaned by GPT (same layout as the 3-colour sheet)
THEMES["gamer_girl4"] = dict(
    THEMES["gamer_girl"],
    label="Gamer girl (private: made for Sally), 4 colours, cleaned by GPT",
    tag_overlap=0.6,                          # = the 4 px sealed strip: the name ring meets the art bottom without covering it and without a gap
    art="art/source_art_gamer_saly4.png",
    palette={"purple": ((107, 4, 117), "purple"), "yellow": ((251, 185, 4), "yellow"), "pink": ((236, 54, 124), "pink"), "white": ((254, 254, 254), "white"),
             "dark": ((15, 15, 15), "purple"), "lpink": ((218, 182, 183), "white"), "mpurple": ((152, 77, 121), "purple")},
    motifs={
        "tag": dict(box=(12, 116, 490, 473), bg="flood", seal=["bottom"], scale=70 / 465, tab_x_px=255,
                    thin=[("yellow", 0.8, "white", (150, 395, 395, 473))],                 # thin yellow slivers along the strap / logo-square outlines
                    absorb=[("yellow", 1.5, "white", (150, 395, 395, 473)), ("yellow", 1.5, "purple", (335, 320, 430, 395))]),   # specks; yellow bits inside the star on the hand   # +4 px: the bottom 4 px strip is sealed and clipped (art ends at 469)
        "bottle": dict(box=(535, 116, 858, 306), bg="flood", seal=["bottom"], scale=48 / 312, tab_x_px=692),
        "pencil_l": dict(box=(24, 702, 138, 826), bg="flood", scale=0.143),
        "pencil_r": dict(box=(460, 722, 620, 815), bg="flood", scale=0.143),
        "ruler_l": dict(box=(62, 998, 265, 1215), bg="purple", scale=0.1422),
        "ruler_r": dict(box=(992, 1000, 1168, 1215), bg="purple", scale=0.1422),
    },
)
THEMES["gamer_girl4"].pop("recolour_near", None)
THEMES["gamer_girl4"].pop("fill_specks", None)

# Sally, 4 colours, GPT round 2 (thicker lines)
THEMES["gamer_girl5"] = dict(
    THEMES["gamer_girl4"],
    label="Gamer girl (private: made for Sally), 4 colours, GPT round 2",
    art="art/source_art_gamer_saly5.png",
    palette={"purple": ((92, 2, 101), "purple"), "yellow": ((251, 185, 4), "yellow"), "pink": ((251, 50, 123), "pink"), "white": ((253, 253, 253), "white"),
             "dark": ((9, 9, 9), "purple"), "lpink": ((212, 177, 189), "white"), "mpurple": ((146, 75, 105), "purple")},
    fill_gaps=[dict(motif="tag", box=(35.0, 0.0, 53.0, 13.0), radius=0.5, priority=["purple", "pink", "white"])],   # no base-colour slivers around the hoodie straps
    thicken=[dict(motif="tag", colour="purple", amount=0.25, box=(37.0, 15.5, 49.0, 23.0)),     # mouth
             dict(motif="tag", colour="white", amount=0.2, box=(35.5, 0.0, 52.5, 12.0))],     # hoodie centre: thin white strap pulls and logo square
    motifs={
        "tag": dict(box=(8, 108, 500, 480), bg="flood", seal=["bottom"], scale=70 / 480, tab_x_px=255),
        "bottle": dict(box=(528, 110, 862, 310), bg="flood", seal=["bottom"], scale=48 / 320, tab_x_px=692),
        "pencil_l": dict(box=(18, 698, 142, 840), bg="flood", scale=0.143),
        "pencil_r": dict(box=(462, 712, 630, 830), bg="flood", scale=0.143),
        "ruler_l": dict(box=(60, 990, 268, 1222), bg="purple", scale=0.1422),
        "ruler_r": dict(box=(972, 990, 1172, 1222), bg="purple", scale=0.1422),
    },
)

# Sally, 4 colours, GPT round 3 (the owner fixed the traced sheet)
THEMES["gamer_girl6"] = dict(
    THEMES["gamer_girl4"],
    label="Gamer girl (private: made for Sally), 4 colours, GPT round 3",
    art="art/source_art_gamer_saly6.png",
    palette={"purple": ((96, 3, 94), "purple"), "yellow": ((251, 192, 4), "yellow"), "yellow2": ((241, 186, 68), "yellow"), "pink": ((247, 42, 117), "pink"),
             "white": ((255, 255, 255), "white"), "lpink": ((191, 144, 186), "white"), "mpurple": ((139, 72, 80), "purple")},
    motifs={
        "tag": dict(box=(8, 108, 500, 478), bg="flood", seal=["bottom"], scale=70 / 485, tab_x_px=255),
        "bottle": dict(box=(522, 110, 858, 308), bg="flood", seal=["bottom"], scale=48 / 327, tab_x_px=692),
        "pencil_l": dict(box=(16, 700, 142, 846), bg="flood", scale=0.1378),
        "pencil_r": dict(box=(462, 712, 636, 832), bg="flood", scale=0.1378),
        "ruler_l": dict(box=(58, 990, 262, 1222), bg="purple", scale=0.1414),
        "ruler_r": dict(box=(972, 990, 1175, 1222), bg="purple", scale=0.1414),
    },
)

# Sally, 4 colours, round 4: the same sheet upscaled to 1911 x 2000 (1.5587 x round 3, same layout)
_F = 1.5587
THEMES["gamer_girl7"] = dict(
    THEMES["gamer_girl6"],
    label="Gamer girl (private: made for Sally), 4 colours, upscaled sheet",
    art="art/source_art_gamer_saly8.png",
    palette={"purple": ((96, 3, 91), "purple"), "yellow": ((250, 192, 6), "yellow"), "yellow2": ((240, 173, 59), "yellow"), "pink": ((244, 43, 118), "pink"),
             "white": ((255, 255, 255), "white"), "lpink": ((244, 197, 199), "white"), "mpurple": ((154, 54, 88), "purple"), "mpink": ((192, 109, 162), "purple")},
    motifs={k: dict(v, box=tuple(int(round(c * _F)) for c in v["box"]),
                    **{"scale": v["scale"] / _F}, **({"tab_x_px": int(round(v["tab_x_px"] * _F))} if "tab_x_px" in v else {}))
            for k, v in THEMES["gamer_girl6"]["motifs"].items()},
)

# Sally, 4 colours, round 5: GPT removed the specks (same size and layout as round 3)
THEMES["gamer_girl8"] = dict(
    THEMES["gamer_girl6"],
    label="Gamer girl (private: made for Sally), 4 colours, specks removed by GPT",
    art="art/source_art_gamer_saly9.png",
    palette={"purple": ((100, 4, 80), "purple"), "yellow": ((251, 189, 4), "yellow"), "yellow2": ((241, 184, 63), "yellow"), "pink": ((248, 49, 115), "pink"),
             "white": ((255, 255, 255), "white"), "lpink": ((205, 152, 190), "white"), "mpurple": ((151, 79, 93), "purple")},
)

THEMES["gamer_girl7"].update(tab_height=3.2, tab_fillet=1.5)   # hanging loop 3.2 mm thick (was 2.2) and smooth joins to the outline

# purple base slab (= the line colour): gaps between art colours show purple, not the yellow; the yellow rim and the loop are yellow regions on top
THEMES["gamer_girl7"].update(outline="purple", tab_colour="yellow", heights={"purple": 2.2, "yellow": 2.8, "pink": 2.8, "white": 3.2},
                             edge_snap=dict(colour="yellow", width=1.0), join_fill=3.0,
                             slots=["white", "pink", "yellow", "purple"])   # AMS: 1 white, 2 pink, 3 yellow, 4 purple

THEMES["gamer"].update(slots=["white", "blue", "red", "black"])   # Osayd AMS order: 1 white, 2 blue, 3 red, 4 black

# Princess (customer girls): GPT sheet 1752 x 897, purple line colour = base slab; the name pill is generated by us, so the sheet's empty name bands, bars and hanging loops are cropped / erased
_PR = dict(bg="flood")
THEMES["princess"] = dict(
    THEMES["gamer_girl7"],
    label="Princess, 4 colours (purple, yellow, pink, white)",
    art="art/source_art_princess.png",
    palette={"purple": ((106, 27, 137), "purple"), "lilac": ((191, 152, 202), "purple"), "mauve": ((158, 81, 135), "purple"),
             "yellow": ((252, 203, 18), "yellow"), "pyellow": ((253, 212, 120), "yellow"),
             "pink": ((242, 75, 129), "pink"), "white": ((254, 254, 254), "white"), "white2": ((243, 243, 243), "white")},
    text_rings=[("purple", 3.0)],
    motifs={
        "tag": dict(box=(268, 56, 922, 326), bg="flood", seal=["bottom"], scale=70 / 654, tab_x_px=590, erase_poly=[[(549, 40), (633, 40), (633, 87), (549, 87)]]),
        "bottle": dict(box=(1022, 102, 1418, 326), bg="flood", seal=["bottom"], scale=48 / 396, tab_x_px=1219),
        "pencil_l": dict(box=(300, 474, 592, 668), bg="flood", scale=0.07, erase=[(512, 524, 595, 556)]),
        "pencil_r": dict(box=(1112, 480, 1450, 672), bg="flood", scale=0.07, erase=[(1112, 524, 1178, 556)]),
        "ruler_l": dict(box=(300, 474, 592, 668), bg="flood", scale=0.09, erase=[(512, 524, 595, 556)]),
        "ruler_r": dict(box=(1112, 480, 1450, 672), bg="flood", scale=0.09, erase=[(1112, 524, 1178, 556)]),
    },
)
for _k in ("edge_snap", "tab_colour"):
    THEMES["princess"].pop(_k, None)
THEMES["princess"].update(smooth=dict(r=0.4, half_w=18.0, depth=18.0, colours=("purple", "yellow")))
THEMES["princess"].update(tab_under_art=["tag"], tab_lift=1.4)   # tag: the yellow crown apex stays visible under the loop (owner chose this look), the loop is lifted 1.4 mm so the wall under the hole stays thick; bottle: loop covers the art
THEMES["princess"].update(ruler=dict(THEMES["gamer_girl7"]["ruler"], rim="yellow"))

# Unicorn (customer girls): GPT sheet 512 x 512 (low resolution: scale ~0.4 mm per px); the line colour is printed as `line` (purple or black)
def _unicorn(line, mane="pink"):
    rgb = {"purple": "#7B3FA0", "black": "#1C1C1C", "yellow": "#F6BA1C", "pink": "#EC407A"}[line]
    th = dict(
        THEMES["princess"],
        label=f"Unicorn, 4 colours ({line} lines, pink, yellow, white)",
        art="art/source_art_unicorn.png",
        outline=line,
        palette={"line": ((30, 91, 216), line), "line2": ((0, 73, 215), line), "mixb": ((108, 112, 215), line), "mixp": ((176, 83, 177), line), "mixw": ((186, 190, 231), line),
                 "pink": ((236, 66, 121), mane), "yellow": ((247, 184, 26), "yellow"), "white": ((255, 255, 255), "white"), "white2": ((242, 242, 242), "white")},
        filament_rgb={"white": "#F2F2F2", "pink": "#EC407A", "yellow": "#F6BA1C", "purple": "#7B3FA0", "black": "#1C1C1C", line: rgb},
        heights={line: 2.2, "yellow": 2.8, mane: 2.8, "white": 3.2},
        text_rings=[(line, 3.0)],
        slots=list(dict.fromkeys(["white", mane, "yellow", line])),
        motifs={
            "tag": dict(box=(78, 20, 230, 184), bg="flood", seal=["bottom"], scale=70 / 152, tab_x_px=150),
            "bottle": dict(box=(343, 52, 462, 166), bg="flood", seal=["bottom"], scale=48 / 119, tab_x_px=400),
            "pencil_l": dict(box=(44, 372, 130, 474), bg="flood", scale=0.15),
            "pencil_r": dict(box=(382, 388, 474, 462), bg="flood", scale=0.13),
            "ruler_l": dict(box=(44, 372, 130, 474), bg="flood", scale=0.30),
            "ruler_r": dict(box=(382, 388, 474, 462), bg="flood", scale=0.30),
        },
    )
    for k in ("smooth", "tab_lift", "tab_under_art"):
        th.pop(k, None)
    th["ruler"] = dict(THEMES["princess"]["ruler"], band=line, body=line, rim={"yellow": "pink", "pink": "yellow"}.get(line, "yellow"))
    return th


THEMES["unicorn_purple"] = _unicorn("purple")
THEMES["unicorn_black"] = _unicorn("black")
THEMES["unicorn_yellow"] = _unicorn("yellow")
THEMES["unicorn_pink"] = _unicorn("pink")
THEMES["unicorn_pinkframe"] = _unicorn("pink", mane="purple")   # pink frame, purple + yellow mane (keeps the mane details)

# Hello Kitty (PRIVATE, a personal gift: Sanrio character, never sold, never published): GPT sheet 1754 x 896, black lines = base slab
THEMES["kitty"] = dict(
    THEMES["princess"],
    label="Kitty (private: personal use only), black / red / yellow / white",
    private=True,
    art="art/source_art_kitty.png",
    outline="black",
    palette={"black": ((5, 5, 5), "black"), "brown": ((76, 55, 48), "black"), "grey": ((143, 144, 144), "black"),
             "red": ((223, 54, 49), "red"), "yellow": ((251, 199, 7), "yellow"),
             "white": ((253, 253, 253), "white"), "white2": ((245, 245, 245), "white")},
    filament_rgb={"white": "#F2F2F2", "red": "#D32F2F", "yellow": "#F6BA1C", "black": "#1C1C1C"},
    heights={"black": 2.2, "red": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "red", "yellow", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="black", body="black", rim="red"),
    motifs={
        "tag": dict(box=(230, 5, 918, 348), bg="flood", seal=["bottom"], scale=70 / 688, tab_x_px=595),
        "bottle": dict(box=(1000, 85, 1520, 368), bg="flood", seal=["bottom"], scale=48 / 520, tab_x_px=1180),
        "pencil_l": dict(box=(262, 508, 612, 672), bg="flood", scale=0.06, erase=[(520, 530, 616, 556)]),
        "pencil_r": dict(box=(1186, 510, 1430, 672), bg="flood", scale=0.06, erase=[(1186, 530, 1276, 556)]),
        "ruler_l": dict(box=(162, 676, 545, 884), bg="flood", scale=0.085),
        "ruler_r": dict(box=(1105, 676, 1590, 861), bg="flood", scale=0.07),
    },
)
for _k in ("smooth", "tab_lift"):
    THEMES["kitty"].pop(_k, None)
THEMES["kitty"].update(tab_under_art=["tag"])   # the loop sits on top of the bow: the bow stays in front

# Kitty with a red frame: the black lines print red, the red bow/hearts print `fill` instead
THEMES["kitty_redframe"] = dict(
    THEMES["kitty"],
    label="Kitty (private), red frame, pink bow and hearts",
    outline="red",
    palette={"black": ((5, 5, 5), "red"), "brown": ((76, 55, 48), "red"), "grey": ((143, 144, 144), "red"),
             "red": ((223, 54, 49), "pink"), "yellow": ((251, 199, 7), "yellow"),
             "white": ((253, 253, 253), "white"), "white2": ((245, 245, 245), "white")},
    filament_rgb={"white": "#F2F2F2", "pink": "#EC407A", "yellow": "#F6BA1C", "red": "#D32F2F"},
    heights={"red": 2.2, "pink": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("red", 3.0)],
    slots=["white", "pink", "yellow", "red"],
    ruler=dict(THEMES["princess"]["ruler"], band="red", body="red", rim="yellow"),
)

# Kitty with a cool-blue (cyan) frame: black lines print cyan, the red bow/hearts print pink
THEMES["kitty_cyanframe"] = dict(
    THEMES["kitty_redframe"],
    label="Kitty (private), cyan frame, pink bow and hearts",
    outline="cyan",
    palette={"black": ((5, 5, 5), "cyan"), "brown": ((76, 55, 48), "cyan"), "grey": ((143, 144, 144), "cyan"),
             "red": ((223, 54, 49), "pink"), "yellow": ((251, 199, 7), "yellow"),
             "white": ((253, 253, 253), "white"), "white2": ((245, 245, 245), "white")},
    filament_rgb={"white": "#F2F2F2", "pink": "#EC407A", "yellow": "#F6BA1C", "cyan": "#14B8D4"},
    heights={"cyan": 2.2, "pink": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("cyan", 3.0)],
    slots=["white", "pink", "yellow", "cyan"],
    ruler=dict(THEMES["princess"]["ruler"], band="cyan", body="cyan", rim="yellow"),
)

# Minnie (PRIVATE, personal gift: Disney character, never sold, never published): flat shapes drawn in code (minnie_art.py), no traced sheet
THEMES["minnie"] = dict(
    THEMES["kitty"],
    label="Minnie-style (private: personal gift), black / red / white / yellow",
    procedural=True,
    motifs={},
    ruler=dict(THEMES["princess"]["ruler"], band="red", body="red", rim="yellow"),   # black ears vanish on a black body, so the ruler body is red and the artwork keeps its black outline
    heights={"black": 2.2, "red": 2.8, "yellow": 2.8, "white": 3.2},
    slots=["white", "red", "yellow", "black"],
)

# Minnie-style from the GPT sheet (PRIVATE, personal gift): navy lines print black, pink bow / hearts, yellow hearts, white face.  Sheet = screenshot cropped at y = 436 (1242 x 914)
_MY = 436
THEMES["minnie_gpt"] = dict(
    THEMES["kitty"],
    label="Minnie-style from GPT sheet (private: personal gift)",
    art="art/source_art_minnie_gpt.png",
    outline="black",
    palette={"black": ((7, 17, 66), "black"), "black2": ((5, 6, 41), "black"), "greyb": ((70, 64, 92), "black"), "greyb2": ((129, 123, 145), "black"),
             "pink": ((231, 115, 160), "pink"), "yellow": ((243, 217, 75), "yellow"),
             "white": ((253, 252, 253), "white"), "greyw": ((196, 193, 210), "white")},
    filament_rgb={"white": "#F2F2F2", "pink": "#EC407A", "yellow": "#F6BA1C", "black": "#1C1C1C"},
    heights={"black": 2.2, "pink": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "pink", "yellow", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="pink", body="pink", rim="yellow"),
    motifs={
        "tag": dict(box=(122, 440 - _MY, 678, 796 - _MY), bg="flood", seal=["bottom"], scale=70 / 556, tab_x_px=412 - 0,
                    erase_poly=[[(380, 430 - _MY), (448, 430 - _MY), (448, 480 - _MY), (380, 480 - _MY)]]),
        "bottle": dict(box=(766, 500 - _MY, 1165, 812 - _MY), bg="flood", seal=["bottom"], scale=48 / 399, tab_x_px=968,
                       erase_poly=[[(945, 495 - _MY), (1000, 495 - _MY), (1000, 548 - _MY), (945, 548 - _MY)]]),
        "pencil_l": dict(box=(170, 940 - _MY, 385, 1092 - _MY), bg="flood", scale=0.10),
        "pencil_r": dict(box=(948, 940 - _MY, 1115, 1080 - _MY), bg="flood", scale=0.10),
        "ruler_l": dict(box=(92, 1122 - _MY, 338, 1294 - _MY), bg="flood", scale=0.14),
        "ruler_r": dict(box=(946, 1122 - _MY, 1194, 1286 - _MY), bg="flood", scale=0.14),
    },
)
THEMES["minnie_gpt"].pop("procedural", None)
THEMES["minnie_gpt"].update(tab_under_art=False)

# Princess girl (customer): GPT sheet (screenshot, cropped to the white sheet 1242 x 1726): navy lines print black, yellow hair, pink crown / hearts / dress, white face
THEMES["princess_girl"] = dict(
    THEMES["minnie_gpt"],
    label="Princess girl with crown (private: for Rafeef)",
    art="art/source_art_rafeef_sheet.png",
    palette={"black": ((6, 16, 62), "black"), "greyb": ((63, 60, 89), "black"), "greyb2": ((116, 113, 146), "black"),
             "yellow": ((245, 220, 74), "yellow"), "dyellow": ((150, 138, 51), "yellow"),
             "pink": ((232, 105, 156), "pink"), "lpink": ((236, 144, 184), "pink"),
             "white": ((253, 253, 253), "white"), "greyw": ((189, 193, 208), "white")},
    motifs={
        "tag": dict(box=(45, 228, 750, 822), bg="flood", seal=["bottom"], scale=70 / 705, tab_x_px=436,
                    erase_poly=[[(340, 120), (530, 120), (530, 230), (340, 230)]]),
        "pencil_l": dict(box=(118, 1052, 450, 1310), bg="flood", scale=0.07, erase=[(446, 1106, 458, 1148)]),
        "pencil_r": dict(box=(972, 1095, 1235, 1325), bg="flood", scale=0.07, erase=[(972, 1105, 992, 1142)]),
        "ruler_l": dict(box=(86, 1333, 392, 1648), bg="flood", scale=0.11, erase=[(86, 1335, 140, 1425), (86, 1352, 215, 1382), (325, 1352, 392, 1382)]),
        "ruler_r": dict(box=(970, 1405, 1234, 1640), bg="flood", scale=0.11),
    },
)
THEMES["princess_girl"].update(tab_under_art=["tag"], tab_lift=1.5)   # the crown's middle ball stays visible under the loop; the loop is lifted so the wall under the hole stays thick

# Princess girl with a purple frame (the black navy lines print purple)
THEMES["princess_girl_purple"] = dict(
    THEMES["princess_girl"],
    label="Princess girl with crown, purple frame (private: for Rafeef)",
    outline="purple",
    palette={k: (v[0], "purple" if v[1] == "black" else v[1]) for k, v in THEMES["princess_girl"]["palette"].items()},
    filament_rgb={"white": "#F2F2F2", "pink": "#EC407A", "yellow": "#F6BA1C", "purple": "#7B3FA0"},
    heights={"purple": 2.2, "pink": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("purple", 3.0)],
    slots=["white", "pink", "yellow", "purple"],
    ruler=dict(THEMES["princess"]["ruler"], band="pink", body="pink", rim="yellow"),
)

# SpongeBob (PRIVATE, personal gift: registered character, never sold, never published): GPT sheet 1024 x 577 kept in art_private/ (not in git), 4 flat colours: black / yellow / brown / white
THEMES["spongebob"] = dict(
    THEMES["kitty"],
    label="SpongeBob-style (private: personal gift), black / yellow / brown / white",
    art="art_private/spongebob.png",
    outline="black",
    palette={"black": ((7, 3, 3), "black"), "dark": ((56, 46, 38), "black"), "brown": ((108, 87, 69), "brown"), "grey": ((136, 140, 127), "brown"),
             "bun": ((206, 158, 76), "yellow"), "yellow": ((243, 210, 50), "yellow"), "pale": ((234, 209, 113), "yellow"), "amber": ((240, 180, 20), "yellow"), "olive": ((150, 150, 60), "yellow"),
             "white": ((253, 253, 253), "white"), "lgrey": ((223, 217, 217), "white"), "pinkish": ((199, 168, 179), "white"), "pink": ((235, 130, 170), "white"),
             "blue": ((60, 110, 190), "black"), "lblue": ((120, 180, 225), "white"), "red": ((200, 30, 40), "brown"), "cheek": ((225, 150, 70), "yellow")},
    filament_rgb={"white": "#F2F2F2", "yellow": "#F6BA1C", "brown": "#7A4A2B", "black": "#1C1C1C"},
    heights={"black": 2.2, "brown": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "yellow", "brown", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="black", body="black", rim="yellow"),
    motifs={
        "tag": dict(box=(140, 14, 516, 222), bg="flood", seal=["bottom"], scale=70 / 376, tab_x_px=335),
        "bottle": dict(box=(596, 8, 905, 240), bg="flood", seal=["bottom"], scale=48 / 309, tab_x_px=745),
        "pencil_l": dict(box=(178, 312, 340, 420), bg="flood", scale=0.12, erase=[(270, 330, 340, 341), (270, 402, 340, 412)]),
        "pencil_r": dict(box=(726, 312, 884, 414), bg="flood", scale=0.12, erase=[(726, 330, 800, 341), (726, 404, 800, 414)]),
        "ruler_l": dict(box=(128, 436, 332, 547), bg="flood", scale=0.20),
        "ruler_r": dict(box=(744, 410, 916, 547), bg="flood", scale=0.20, erase=[(744, 424, 826, 440)]),
    },
)
THEMES["spongebob"].update(tab_under_art=False)

# every customer / private tag is scaled to a similar size (height kept between 62 and 76 mm, width up to 76 mm), so the packs look consistent
for _k in ("princess", "unicorn_purple", "unicorn_black", "unicorn_yellow", "unicorn_pink", "unicorn_pinkframe", "kitty", "kitty_redframe", "kitty_cyanframe",
           "minnie", "minnie_gpt", "princess_girl", "princess_girl_purple", "spongebob"):
    if _k in THEMES:
        THEMES[_k]["tag_fit"] = dict(hmin=62.0, hmax=76.0, wmax=76.0)

# Lightning-McQueen-style race car (PRIVATE, personal gift: registered character, never sold, never published): art in art_private/ (not in git)
THEMES["mcqueen"] = dict(
    THEMES["kitty"],
    label="Race car (private: personal gift), black / red / yellow / white",
    art="art_private/mcqueen.png",
    outline="black",
    palette={"black": ((0, 0, 0), "black"), "dark": ((60, 40, 40), "black"), "brown": ((140, 90, 40), "black"),
             "red": ((215, 30, 35), "red"), "dred": ((150, 20, 20), "red"), "pink": ((235, 120, 120), "red"),
             "white": ((253, 253, 253), "white"), "lgrey": ((215, 215, 220), "white"), "grey": ((140, 140, 145), "white"), "lblue": ((170, 205, 235), "white"),
             "yellow": ((250, 200, 40), "yellow"), "gold": ((210, 150, 20), "yellow")},
    filament_rgb={"white": "#F2F2F2", "red": "#D32F2F", "yellow": "#F6BA1C", "black": "#1C1C1C"},
    heights={"black": 2.2, "red": 2.8, "yellow": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "red", "yellow", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="black", body="black", rim="red"),
    motifs={
        "tag": dict(box=(145, 6, 528, 207), bg="flood", seal=["bottom"], scale=70 / 383, tab_x_px=335,
                    erase=[(312, 4, 360, 76), (140, 104, 204, 180), (462, 110, 528, 180)],
                    move=[(170, 18, 266, 127, 0, 12), (266, 18, 290, 90, 0, 12)]),   # the top bolt (under the loop) and the two floating side bolts,
        "bottle": dict(box=(608, 78, 932, 228), bg="flood", seal=["bottom"], scale=48 / 324, tab_x_px=745),
        "pencil_l": dict(box=(144, 110, 200, 178), bg="flood", scale=0.16),
        "pencil_r": dict(box=(764, 440, 852, 546), bg="flood", scale=0.12),
        "ruler_l": dict(box=(104, 438, 328, 547), bg="flood", scale=0.20),
        "ruler_r": dict(box=(760, 436, 950, 547), bg="flood", scale=0.20),
    },
)
THEMES["mcqueen"].update(tab_under_art=False, tag_fit=dict(hmin=62.0, hmax=76.0, wmax=76.0))

def _star7(cx, cy, ro, ri):
    """7-pointed star polygon (source px) pointing up: the Jordanian flag star."""
    import math
    return [(round(cx + (ro if i % 2 == 0 else ri) * math.cos(math.radians(-90 + i * 360 / 14))),
             round(cy + (ro if i % 2 == 0 else ri) * math.sin(math.radians(-90 + i * 360 / 14)))) for i in range(14)]


# Football (Jordan flag colours): generic footballer, not a registered character, so this one may be sold.  Sheet 1024 x 577, 4 colours: black / red / green / white (gold items print white)
THEMES["football"] = dict(
    THEMES["kitty"],
    label="Football (Jordan flag colours), black / red / green / white",
    private=False,
    art="art/source_art_football.png",
    outline="black",
    palette={"black": ((10, 10, 10), "black"), "dark": ((60, 45, 40), "black"), "hair": ((130, 80, 50), "black"),
             "red": ((200, 30, 40), "red"), "dred": ((150, 25, 30), "red"),
             "green": ((30, 130, 60), "green"), "dgreen": ((20, 90, 45), "green"),
             "white": ((253, 253, 253), "white"), "skin": ((235, 190, 150), "white"), "gold": ((225, 175, 30), "white"), "grey": ((170, 170, 175), "white"), "lgrey": ((220, 220, 225), "white")},
    filament_rgb={"white": "#F2F2F2", "red": "#D32F2F", "green": "#2E9E4F", "black": "#1C1C1C"},
    heights={"black": 2.2, "red": 2.8, "green": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "red", "green", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="black", body="black", rim="red"),
    motifs={
        "tag": dict(box=(120, 4, 530, 207), bg="flood", seal=["bottom"], scale=70 / 396, tab_x_px=330,
                    recolour_dark=[(408, 110, 454, 164, (30, 130, 60))],
                    erase=[(122, 96, 205, 182)],                                  # the old flag
                    insert=[("art/jordan_flag.png", 122, 102, 226, 170)],
                    paint_poly=[("white", _star7(140, 144, 8.5, 4.2))]),        # the exact flag the owner chose (seven-pointed star, wavy), ringed by flag_rings
        "bottle": dict(box=(608, 34, 920, 232), bg="flood", seal=["bottom"], scale=48 / 312, tab_x_px=760),
        "pencil_l": dict(box=(418, 30, 494, 110), bg="flood", scale=0.14),   # the ball replaces the whistle
        "pencil_r": dict(box=(796, 436, 914, 538), bg="flood", scale=0.10),
        "ruler_l": dict(box=(124, 436, 262, 548), bg="flood", scale=0.20),
        "ruler_r": dict(box=(890, 388, 1018, 538), bg="flood", scale=0.20, erase=[(890, 386, 1018, 545)],
                        insert=[("art/jordan_flag.png", 906, 400, 1000, 462)],
                        paint_poly=[("white", _star7(922, 438, 8, 4))]),
    },
)
THEMES["football"]["flag_rings"] = [dict(motif="tag", box=(1.0, 3.0, 20.5, 19.0), gap=0.0, width=1.0, colour="white", max_area=400),
                                   dict(motif="ruler_r", box=(1.0, 8.0, 26.0, 30.0), gap=0.0, width=1.0, colour="white", max_area=400)]
THEMES["football"].update(tab_under_art=False, sil_close=9.0, tag_fit=dict(hmin=62.0, hmax=76.0, wmax=76.0))

# Football with black and white swapped: white backing + white lettering ring, black letters and black artwork lines on top
_fb = THEMES["football"]
_sw = {"black": "white", "white": "black"}
THEMES["football_inv"] = dict(
    _fb,
    label="Football, black and white swapped (white backing, black letters)",
    outline="white",
    letters="black",
    palette={k: (v[0], _sw.get(v[1], v[1])) for k, v in _fb["palette"].items()},
    heights={"white": 2.2, "red": 2.8, "green": 2.8, "black": 3.2},
    text_rings=[("white", 3.0)],
    slots=["white", "red", "green", "black"],
    ruler=dict(_fb["ruler"], band="white", body="white", rim="red", ticks="black"),
)

# Football on a WHITE backing: the artwork keeps its colours and gets a drawn black outline (art_ring) around the face, flag, ball ...; letters black
THEMES["football_white"] = dict(
    _fb,
    label="Football, white backing with black outlines",
    outline="white",
    letters="black",
    heights={"white": 2.2, "red": 2.8, "green": 2.8, "black": 2.8},
    text_rings=[("white", 3.0)],
    slots=["white", "red", "green", "black"],
    ruler=dict(_fb["ruler"], band="white", body="white", rim="red", ticks="black"),
    art_ring=dict(colour="black", width=1.0, colours=["white", "red", "green"]),
)
import copy as _copy
THEMES["football_white"]["motifs"] = _copy.deepcopy(_fb["motifs"])
THEMES["football_white"]["motifs"]["tag"]["erase"] = [(382, 54, 426, 118), (390, 164, 432, 210)]   # the thin motion lines of the kick (they only clutter the outlined version)
THEMES["football_white"]["motifs"]["pencil_l"]["box"] = (426, 30, 494, 110)   # ball without the motion lines

# Spider-hero (PRIVATE, personal gift: registered character, never sold): GPT sheet 1280 x 720 kept in art_private/ (not in git); 4 colours black / red / blue / white (yellow stars print white)
THEMES["spiderman"] = dict(
    THEMES["kitty"],
    label="Spider-hero (private: personal gift), black / red / blue / white",
    art="art_private/spiderman.jpg",
    outline="black",
    palette={"black": ((6, 3, 4), "black"), "dark": ((66, 10, 10), "black"), "red": ((221, 30, 31), "red"), "dred": ((154, 37, 36), "red"),
             "blue": ((6, 69, 154), "blue"), "white": ((254, 254, 254), "white"), "yellow": ((248, 192, 14), "white"),
             "grey": ((169, 168, 168), "white"), "dgrey": ((98, 97, 93), "black"), "lgrey": ((222, 222, 226), "white")},
    filament_rgb={"white": "#F2F2F2", "red": "#D32F2F", "blue": "#1E5BD8", "black": "#1C1C1C"},
    heights={"black": 2.2, "red": 2.8, "blue": 2.8, "white": 3.2},
    text_rings=[("black", 3.0)],
    slots=["white", "red", "blue", "black"],
    ruler=dict(THEMES["princess"]["ruler"], band="black", body="black", rim="blue"),
    motifs={
        "tag": dict(box=(170, 2, 662, 266), bg="flood", seal=["bottom"], scale=70 / 492, tab_x_px=360,
                    erase=[(176, 116, 264, 202), (566, 132, 648, 208)]),   # the two hearts: replaced by spider webs
        "bottle": dict(box=(755, 28, 1132, 296), bg="flood", seal=["bottom"], scale=48 / 377, tab_x_px=950),
        "pencil_l": dict(box=(350, 428, 430, 506), bg="flood", scale=0.14, erase=[(350, 428, 372, 432)]),
        "pencil_r": dict(box=(972, 402, 1096, 516), bg="flood", scale=0.10, erase=[(972, 412, 990, 428), (972, 498, 990, 516)]),
        "ruler_l": dict(box=(160, 546, 324, 700), bg="flood", scale=0.18),
        "ruler_r": dict(box=(1000, 542, 1150, 682), bg="flood", scale=0.18, erase=[(1000, 536, 1150, 548)]),
    },
)
THEMES["spiderman"]["thicken"] = [dict(motif="tag", colour="black", amount=0.3, box=(14.0, 8.0, 41.0, 37.0)),
                                  dict(motif="bottle", colour="black", amount=0.42, box=(10.0, 8.0, 40.0, 34.0)),
                                  dict(motif="ruler_l", colour="black", amount=0.4, box=(3.0, 7.0, 27.0, 27.0))]
THEMES["spiderman"]["webs"] = [dict(motif="tag", colour="white", at=[(7.5, 14.8, 5.4), (62.0, 13.6, 5.4)], w=0.42)]
THEMES["spiderman"].pop("flag_rings", None)
THEMES["spiderman"].update(tab_under_art=False, sil_close=5.0, tag_fit=dict(hmin=62.0, hmax=76.0, wmax=76.0))

BASE_THEMES = [k for k, v in THEMES.items() if "variant_of" not in v and not v.get("private")]   # sold themes (catalog, site, orders)
PRIVATE_THEMES = [k for k, v in THEMES.items() if v.get("private")]


def resolve_theme(base, colours=4):
    """('construction', 3) -> 'construction3'; 4 colours is the base theme itself."""
    if colours == 4:
        return base
    key = f"{base}{colours}"
    if key not in THEMES:
        raise ValueError(f"theme {base!r} has no {colours}-colour version (choose 2, 3 or 4)")
    return key
