# -*- coding: utf-8 -*-
"""Are the out-of-view tick labels that MultipleLocator returns painted?"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import figstyle as st
CAP = []
st.save_fig = lambda fig, stem, *a, **k: (CAP.append((os.path.basename(stem), fig)), [])[1]
import figs7_ecdf as F
F.main()
im = np.asarray(Image.open(os.path.join(os.path.dirname(HERE), "figures",
                                        "FigureS7_ecdf.png")).convert("L"))
print("png", im.shape)
S = im.shape[1] / 709.0
for name, fig in CAP:
    if name != "FigureS7_ecdf":
        continue
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    H = fig.canvas.get_height_height() if False else fig.canvas.get_width_height()[1]
    for k, ax in enumerate(fig.axes):
        ab = ax.get_window_extent(renderer=r)
        x0, x1 = ax.get_xlim()
        for t in ax.get_xticklabels():
            v = float(t.get_position()[0])
            if x0 <= v <= x1:
                continue
            b = t.get_window_extent(renderer=r)
            # sample the label's box in the delivered PNG
            px0, px1 = int(b.x0 * S) + 2, int(b.x1 * S) - 2
            py0, py1 = int((H - b.y1) * S) + 2, int((H - b.y0) * S) - 2
            py0 = max(py0, 0); py1 = min(py1, im.shape[0])
            if px1 <= px0 or py1 <= py0:
                print("  ax[%d] %r fully off-canvas" % (k, t.get_text()))
                continue
            win = im[py0:py1, max(px0, 0):min(px1, im.shape[1])]
            dark = int((win < 200).sum())
            print("  ax[%d] tick %r value %.2f at x %6.1f..%6.1f : %d dark px"
                  % (k, t.get_text(), v, b.x0, b.x1, dark))
plt.close("all")
