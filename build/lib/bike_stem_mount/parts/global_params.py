from build123d import MM

# ================== GLOBAL PARAMETERS ==================
# 3D printing basics
tol = 0.2 * MM  # Tolerance
wall_min = 0.4 * MM  # Minimum wall width
wall = wall_min * 3 * MM  # Recommended width for most walls of this print
eps = 1e-5 * MM  # A small number
screw_floating_cut = 2 * MM  # How much free space between screw-connected parts
