import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.lines import Line2D

from icecream import ic, install
install()

from wonka.utils import *

def sim_lin(p_lcs, p_c1, p_c2):
    """Lin similarity between two concepts lying in the same knowledge graph."""
    IC = lambda p: -np.log(p)
    return 2 * IC(p_lcs) / (IC(p_c1) + IC(p_c2))

n_samples = 1000
p_c2 = np.linspace(1e-2, 1, n_samples)
p_lcs = np.linspace(1e-2, 1, n_samples)

X, Y = np.meshgrid(p_c2, p_lcs)

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

lines = []
ccolors = ["black", "purple", "blue", "green", "orange", "red"]
for i, p_c1 in enumerate([1e-1, 2e-1, 3e-1, 4e-1, 5e-1, 6e-1]):
    Z = sim_lin(Y, p_c1, X)
    surf = ax.plot_surface(X, Y, Z, color=ccolors[i%len(ccolors)], alpha=.8, lw=0)
    lines.append(Line2D([0], [0], color=ccolors[i % len(ccolors)], lw=2, label=fr"$p(c_1)={int(p_c1*100)}\%$"))

ax.legend(handles=lines, loc='center left', bbox_to_anchor=(.6, .7))
elev, azim, roll = 30, 30, 0
ax.view_init(elev, azim, roll)

ax.set_xlabel(r"$p(c_2)$", fontdict={"fontsize": 16})
ax.set_ylabel(r"$p(LCS(c_1, c_2))$", fontdict={"fontsize": 16})
ax.set_zlabel(r"$\mathrm{sim}_{lin}(c_1, c_2)$", fontdict={"fontsize": 16})

ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))

ax.set_xticklabels(ax.get_xticklabels(), fontsize=12)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=12)
ax.set_zticklabels(ax.get_zticklabels(), fontsize=12)

# Clear frame
ax.grid(False)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.xaxis.set_pane_color("white")
ax.yaxis.set_pane_color("white")

plt.get_current_fig_manager().full_screen_toggle()
plt.tight_layout()
plt.savefig("sim_lin.png", dpi=300)

plt.show()