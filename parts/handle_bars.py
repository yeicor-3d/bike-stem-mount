# %%
from contextlib import suppress
from build123d import *
import math
try:
    from global_params import *
    from stem import stem_height, stem_side_faces
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.stem import stem_height, stem_side_faces
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== PARAMETERS ==================

handlebar_side_xy = (80, 25)  # (center, start)
handlebar_size = (10, wall)  # (width, height)
handlebar_rot = 5  # Rotation of the handlebar (degrees)
handlebar_rad = 16  # Radius of the handlebar

# ================== MODELLING ==================

handlebar_side_loc = Location(
    (handlebar_side_xy[0], handlebar_side_xy[1], stem_height), (0, 90, 90))
with BuildSketch(handlebar_side_loc) as handlebar_side:
    Rectangle(handlebar_size[0], handlebar_size[1],
              align=Align.MIN, rotation=-handlebar_rot)
with BuildPart() as handlebar_side_conn:
    conn_base = stem_side_faces.group_by(Axis.Y)[-1].face()
    del stem_side_faces
    edge_left = conn_base.edges().group_by(SortBy.LENGTH)[-3].edge()
    edge_bottom = conn_base.edges().group_by(SortBy.LENGTH)[-2].edge()
    extra_vert_rectangle = edge_bottom@0 + (edge_left@1 - edge_left@0)
    edge_right = Edge.make_line(edge_bottom@0, extra_vert_rectangle)
    edge_top = Edge.make_line(extra_vert_rectangle, edge_left@1)
    face = Face.make_from_wires(Wire.make_wire(
        [edge_left, edge_top, edge_right, edge_bottom]))
    face_loc = Location(edge_bottom@1)
    del conn_base
    del edge_top
    del edge_right
    del edge_left
    del edge_bottom
    del extra_vert_rectangle
    with BuildLine() as handlebar_side_conn_path:
        Spline(face_loc.position,
               handlebar_side_loc.position,
               tangents=[(0, 1, 0), Vector(1, 0, -0.1).normalized()],
               tangent_scalars=[.5, 1])
    sweep(sections=[handlebar_side.sketch, face],
          path=handlebar_side_conn_path, multisection=True)
    del face
    del face_loc
    del handlebar_side_conn_path
    del handlebar_side_loc

save = handlebar_side_conn.faces().group_by(Axis.X)[-1].face().center_location
with BuildPart() as handle_bar_core:
    with BuildSketch(save):
        Rectangle(handlebar_size[1], handlebar_size[0],
                  rotation=-handlebar_rot)
    revolve(axis=Axis(save.position - (0, 0, handlebar_rad +
                                       handlebar_size[1]/2), (0, 1, 0)))
    del save
handlebar_side_conn.part += handle_bar_core.part
del handle_bar_core
del handlebar_side

# Join a mirrored version of the handlebar side
with BuildPart() as handle_bars_part:
    add(handlebar_side_conn)

    add(mirror(objects=handlebar_side_conn.part))
    del handlebar_side_conn

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# # %%
