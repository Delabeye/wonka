import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Create sample data for X, Y, Z
X = np.linspace(0, 10, 100)
Y = np.linspace(0, 10, 100)
X, Y = np.meshgrid(X, Y)
Z = np.sin(np.sqrt(X**2 + Y**2))

ccolors = ["black", "purple", "blue", "green", "orange", "red"]
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

for i, p_c1 in enumerate([1e-1, 2e-1, 3e-1, 4e-1, 5e-1, 6e-1]):
    surf = ax.plot_surface(X, Y, Z, color=ccolors[i % len(ccolors)], alpha=0.8, linewidth=0, label=f"p_c1={p_c1:.2f}")

ax.legend()
plt.show()