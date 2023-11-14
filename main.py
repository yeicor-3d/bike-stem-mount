#%%
from build123d import *

try: # Optional, for visualizing the model in VSCode instead of CQ-editor or exporting to STL
  from ocp_vscode import show_object, show_all, reset_show, set_port
  set_port(3939)
except ImportError:
  pass

#%%
# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended width for most walls of this print
eps = 1e-5  # A small number

# Measurements...
stem_screw_radius = 2.0  # Diameter of the screw that connects the stem to the fork
stem_circle_flat_radius = 10.0  # Radius of the flat part of the circle
stem_circle_radius = 16  # Radius of the circle
stem_circle_max_height = 3.0  # Maximum height of the circle
stem_rect = (35, 35)  # Stem "rectangle"
# Where to connect to the stem from the center of the circle
stem_range = (20, 45)
stem_fillet = 5.0  # Fillet radius of the stem (square -> circle)
# How much to overlap the stem with our model for a stronger connection
stem_clip = (stem_fillet, 2.0)

#%%
# ================== MODELLING ==================

with BuildPart() as obj:

    # Stem screw circular connector
    with BuildSketch():
        Circle(radius=stem_circle_flat_radius)
        Circle(radius=stem_screw_radius, mode=Mode.SUBTRACT)
    with BuildSketch(Plane.XY.move(Location((0, 0, stem_circle_max_height)))):
        Circle(radius=stem_circle_radius)
        Circle(radius=stem_circle_flat_radius, mode=Mode.SUBTRACT)
    extrude(amount=wall)
    with BuildSketch(Plane.XY.move(Location((0, 0, stem_circle_max_height + wall)))):
        Circle(radius=stem_circle_radius+wall)
        Circle(radius=stem_circle_radius, mode=Mode.SUBTRACT)
        Circle(radius=stem_circle_flat_radius)
        Circle(radius=stem_circle_flat_radius-wall, mode=Mode.SUBTRACT)
    extrude(amount=-(stem_circle_max_height + wall))
    chamfer_edge = obj.faces().filter_by(Axis.Z).group_by(SortBy.AREA)[-4].edges().group_by(SortBy.LENGTH)[-1]
    chamfer(chamfer_edge, stem_circle_flat_radius - stem_screw_radius - wall - eps - 1, stem_circle_max_height-eps)
    del chamfer_edge

    # Stem fitting
    stem_distance = stem_range[1] - stem_range[0]
    with BuildSketch(Plane.YZ.move(Location((stem_range[1], 0, 0)))):
        Rectangle((stem_circle_radius + wall)*2-eps, wall, align=(Align.CENTER, Align.MIN))
    extrude(until=Until.PREVIOUS)
    with BuildSketch(Plane.XY.move(Location((stem_circle_radius, 0, 0)))):
        Rectangle(stem_range[1] - stem_circle_radius, stem_rect[0], align=(Align.MIN, Align.CENTER))
    extrude(amount=wall)


# ================== SHOWING/EXPORTING ==================

if 'reset_show' in locals() and 'show_all' in locals():
    reset_show()
    show_all()
elif 'show_object' in locals():
    show_object(obj, 'bike-stem-mount')
else:
    obj.part.export_stl('bike-stem-mount.stl')

# %%
