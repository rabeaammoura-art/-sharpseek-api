import numpy as np, itertools, math
exec(open('split_search2.py').read().split('if __name__')[0])
import split_search2 as _x  # noqa (only for TW/TH names)
res=[]
for TWv,THv in ((30.6,30.2),(30.0,29.5)):
    TW,TH=TWv,THv
    best=None
    for x1 in np.arange(26,34.01,0.5):
        for x2 in np.arange(56,66.01,0.5):
            for y in np.arange(15,32.01,0.5):
                lines=[(0.0,x1),(0.0,x2),(math.pi/2,y)]
                e=evaluate(lines)
                if e and (best is None or e[:2]<best[:2]): best=e+(x1,x2,y)
    print(f"bed {TWv}x{THv}:", "none" if not best else f"regions={best[0]:.1f}, cuts x={best[3]:.1f}/{best[4]:.1f} cm, y={best[5]:.0f} cm, material crossings {best[1]:.0f}")
