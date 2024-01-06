# %%
from contextlib import suppress
from build123d import *
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
    face = stem_side_faces.group_by(Axis.Y)[-1].face()
    del stem_side_faces
    face_loc = Location(face.edges().group_by(
        SortBy.LENGTH)[-1].group_by(Axis.Z)[0].edge()@1)
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

handle_bars_part = handle_bars_part.part

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# # %%
