import cadquery as cq

# debug = lambda *args, **kwargs: None
# show_object = lambda *args, **kwargs: None

# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended width for most walls of this print
eps = 1e-5  # A small number

# ...

# ================== MODELLING ==================

obj = cq.Workplane("XY").box(10, 10, 10)

show_object(obj)
