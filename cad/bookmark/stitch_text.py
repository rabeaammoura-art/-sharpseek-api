"""Hand-drawn cross-stitch lettering 'اقرأ وارتق' (one stitch per cell, like tatreez names). Image reads right to left."""
# rows 0..10, baseline row 8. '#' = stitch. Drawn left -> right as seen (Arabic starts at the right end).
GLYPHS = {
    "tq": [  # تق : final qaf (left) joined to initial ta (right)
        "............",
        "............",
        "............",
        ".........#.#",
        "....#.#.....",
        "..........#.",
        "....###...#.",
        "#...#.#...#.",
        "#...#######.",
        "#...#.......",
        ".###........",
    ],
    "ra": [
        "...", "...", "...", "...", "...", "...", "...",
        "..#",
        "..#",
        ".#.",
        "#..",
    ],
    "alef": ["." , "#", "#", "#", "#", "#", "#", "#", "#", ".", "."],
    "waw": [
        "....", "....", "....", "....", "....",
        ".###",
        ".#.#",
        ".###",
        "...#",
        "..#.",
        "##..",
    ],
    "alef_hamza": [
        "##", "#.", "..",
        "#.", "#.", "#.", "#.", "#.", "#.", "..", "..",
    ],
    "qr": [  # قر : final ra (left) joined to initial qaf (right)
        ".......",
        ".......",
        ".......",
        ".......",
        "....#.#",
        ".......",
        "....###",
        "....#.#",
        "..#####",
        ".#.....",
        "#......",
    ],
}
GAP, WORD_GAP = 2, 4
# left -> right in the image: وارتق (as تق, ر, ا, و) then the word gap then اقرأ (as أ, قر, ا)
LINE = [["tq", "ra", "alef", "waw"], ["alef_hamza", "qr", "alef"]]


def image():
    cols = [[] for _ in range(11)]
    first_word = True
    for word in LINE:
        if not first_word:
            for r in range(11):
                cols[r] += ["."] * WORD_GAP
        first_word = False
        for k, g in enumerate(word):
            if k:
                for r in range(11):
                    cols[r] += ["."] * GAP
            rows = GLYPHS[g]
            w = max(len(x) for x in rows)
            for r in range(11):
                cols[r] += list(rows[r].ljust(w, "."))
    return ["".join(r) for r in cols]


def cells(c0, r0, rotate="ccw"):
    """stitch cells on the bookmark; ccw = reads top -> bottom, letter tops facing left."""
    img = image()
    W = len(img[0])
    out = set()
    for y, row in enumerate(img):
        for x, ch in enumerate(row):
            if ch == "#":
                if rotate == "ccw":
                    out.add((c0 + y, r0 + (W - 1 - x)))
                else:
                    out.add((c0 + (10 - y), r0 + x))
    return out, W


if __name__ == "__main__":
    for r in image():
        print(r)
