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
                             slots=["purple", "white", "yellow", "pink"])   # AMS: 1 purple, 2 white, 3 yellow, 4 pink

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
