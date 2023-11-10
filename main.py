from build123d import *


# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended width for most walls of this print
eps = 1e-5  # A small number

# Measurements...


# ================== MODELLING ==================

# Build the button by layers from front-facing (on the XY plane) to back-facing (up the Z axis)
with BuildPart() as obj:
    # The hole for the nut
    with BuildSketch():
        Circle(radius=3)
        RegularPolygon(2, major_radius=False, side_count=6, mode=Mode.SUBTRACT)
    extrude(amount=1)


# ================== SHOWING/EXPORTING ==================

if 'show_object' in locals():
    show_object(obj, 'bike-stem-mount')
else:
    obj.part.export_stl('bike-stem-mount.stl')
