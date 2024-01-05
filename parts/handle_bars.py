# %%
from contextlib import suppress
from build123d import *
from copy import copy, deepcopy
import math
try:
    from global_params import *
    from stem import stem_height, stem_part_core
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.stem import stem_height, stem_part_core
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== PARAMETERS ==================

stem_angle = 20  # Stem angle wrt the headset
stem_rect = (35, 35)  # Stem "rectangle" (horizontal, vertical)
# Where to connect to the stem from the center of the circle
stem_range = (20, 45)
stem_fillet = 5.0  # Fillet radius of the stem (square -> circle)
# How much to overlap the stem with our model for a stronger connection
stem_clip = (stem_fillet, 2.0)

handlebar_side_xy = (60, 20)  # (center, start)
handlebar_size = (10, wall)  # (width, height)

# ================== MODELLING ==================

handlebar_side_loc = Location(
    (handlebar_side_xy[0], handlebar_side_xy[1], stem_height), (0, 90, 90))
with BuildSketch(handlebar_side_loc) as handlebar_side:
    Rectangle(handlebar_size[0], handlebar_size[1], align=Align.MIN)
with BuildPart() as handlebar_side_conn:
    conn_base = sum(stem_part_core.faces().group_by(
        Axis.Y)[-3:], ShapeList())
    conn_base -= conn_base.faces().group_by(Axis.X)[0]
    edge_left_verts = conn_base.vertices().group_by(Axis.X)[-1]
    edge_left_verts -= edge_left_verts.group_by(Axis.Y)[-1]
    edge_top = conn_base.edges().group_by(
        SortBy.LENGTH)[-1].group_by(Axis.Z)[-1].edge()
    edge_right = Edge.make_line(
        edge_top@0, edge_top@0 - (0, 0, abs(edge_left_verts[1].Z - edge_left_verts[0].Z)))
    edge_left = Edge.make_line(
        edge_top@1, edge_top@1 - (0, 0, abs(edge_left_verts[1].Z - edge_left_verts[0].Z)))
    edge_bottom = Edge.make_line(edge_left@1, edge_right@1)
    face = Face.make_from_wires(Wire.make_wire(
        [edge_left, edge_top, edge_right, edge_bottom]))
    face_loc = Location(edge_bottom@0)
    del conn_base
    del edge_left_verts
    del edge_top
    del edge_right
    del edge_left
    del edge_bottom
    with BuildLine() as handlebar_side_conn_path:
        Spline(face_loc.position,
               handlebar_side_loc.position,
               tangents=[(0, 1, 0), (1, 0, 0)],
               tangent_scalars=[.5, 1])
    sweep(sections=[handlebar_side.sketch, face],
          path=handlebar_side_conn_path, multisection=True)
    del face
    del face_loc
    del handlebar_side_conn_path
    del handlebar_side_loc
    del handlebar_side

# Join a mirrored version of the handlebar side
with BuildPart() as handle_bars_part:
    add(handlebar_side_conn)
    add(mirror(objects=handlebar_side_conn.part))

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# %%
