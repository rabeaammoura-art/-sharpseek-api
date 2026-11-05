"""Estimate a depth map for one person's crop (Depth Anything V2, small) and cache it as .npy.

Usage: python depth.py <image> <girl|boy> <out.npy>
The map is relative inverse depth (bigger = closer), same size as the crop.
"""
import sys

import cv2
import numpy as np
import torch
from PIL import Image
from transformers import pipeline

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from hueforge import PEOPLE  # noqa: E402

MODEL = "depth-anything/Depth-Anything-V2-Small-hf"

if __name__ == "__main__":
    image, who, out = sys.argv[1:4]
    x0, y0, x1, y1 = PEOPLE[who]["crop"]
    img = cv2.imread(image)[y0:y1, x0:x1]
    pil = Image.fromarray(img[..., ::-1])
    torch.set_num_threads(4)
    pipe = pipeline("depth-estimation", model=MODEL, device="cpu")
    # run at ~2x the crop for detail on the face; the model works on 518 px patches internally
    big = pil.resize((pil.width * 2, pil.height * 2), Image.BICUBIC)
    d = pipe(big)["predicted_depth"].squeeze().numpy().astype(np.float32)
    d = cv2.resize(d, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    np.save(out, d)
    print(out, d.shape, float(d.min()), float(d.max()))
