# -*- coding: utf-8 -*-
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import figstyle as st
CAP = []
st.save_fig = lambda fig, stem, *a, **k: (CAP.append((os.path.basename(stem), fig)), [])[1]
import fig4_forward as F
F.build("journal")
for name, fig in CAP:
    fig.canvas.draw(); r = fig.canvas.get_renderer()
    print("=== %s" % name)
    for k, ax in enumerate(fig.axes):
        ytl = [(t.get_text(), t.get_visible()) for t in ax.get_yticklabels()]
        print("  ax[%d] ylim %-40s yticks %s" % (k, ax.get_ylim(), ytl))
    # locate the '−2000' artist
    for t in fig.findobj(matplotlib.text.Text):
        if "2000" in t.get_text():
            print("  FOUND %r visible=%s axes=%r parent=%r clip_on=%s"
                  % (t.get_text(), t.get_visible(), t.axes,
                     type(t.get_parent()).__name__, t.get_clip_on()))
            bb = t.get_window_extent(renderer=r)
            print("     bbox", bb.x0, bb.x1, bb.y0, bb.y1)
            try:
                print("     clipbox", t.get_clip_box().bounds)
            except Exception as e:
                print("     clipbox n/a", e)
plt.close("all")
