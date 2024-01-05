# %%
from contextlib import suppress
from build123d import *
from copy import copy, deepcopy
import math
try:
    from global_params import *
    from headset_screw_part import headset_screw_part, stem_circle_max_height, stem_circle_radius
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.headset_screw_part import headset_screw_part, stem_circle_max_height, stem_circle_radius
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

handlebar_side_xy = (60, 30)  # (center, start)
handlebar_size = (10, wall)  # (width, height)

# ================== MODELLING ==================


def unique_ordered(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


# Uglily recreate conn_face to support sweeping...
conn_face = headset_screw_part.faces().group_by(Axis.X)[-1].face()
del headset_screw_part
conn_face_bb = conn_face.bounding_box()
with BuildSketch() as sweep_obj:
    with BuildLine() as sweep_obj_line:
        Polyline((conn_face_bb.min.Z, conn_face_bb.min.Y), (conn_face_bb.max.Z, conn_face_bb.min.Y),
                 (conn_face_bb.max.Z, conn_face_bb.max.Y), (conn_face_bb.min.Z, conn_face_bb.max.Y), close=True)
    make_face()

    to_fillet = sweep_obj_line.vertices().group_by(Axis.X)[-1]
    fillet(objects=to_fillet, radius=stem_circle_max_height-wall)
    to_fillet = sweep_obj_line.vertices().group_by(Axis.X)[0]
    fillet(objects=to_fillet, radius=wall)
    del sweep_obj_line
    del to_fillet

    # Validate exact sketch matches...
    with BuildSketch() as match:
        add(sweep_obj)
        add(conn_face, mode=Mode.SUBTRACT)
        assert len(match.vertices()
                   ) == 0, "Rebuilt face sketch doesn't match original"
        add(conn_face)
        add(sweep_obj, mode=Mode.SUBTRACT)
        assert len(match.vertices()
                   ) == 0, "Rebuilt face sketch doesn't match original"
    del match

stem_dist = stem_range[1] - stem_range[0]
stem_height = stem_dist * math.tan(math.radians(stem_angle))
print(stem_height)
with BuildLine() as sweep_path:
    Polyline((0, 0, stem_circle_radius),
             (0, 0, stem_range[0]), (stem_height, 0, stem_range[1]))

stem_and_handle_bars_part = sweep(sections=sweep_obj, path=sweep_path)
conn_face_loc = copy(conn_face.center_location)
stem_and_handle_bars_part = stem_and_handle_bars_part.moved(
    Location(conn_face_loc.position - (0, 0, conn_face_bb.size.Z/2), (180, 90, 0)))
del sweep_obj
del sweep_path
del conn_face_loc
del conn_face
del conn_face_bb

handlebar_side_loc = Location(
    (handlebar_side_xy[0], handlebar_side_xy[1], stem_height), (0, 90, 90))
with BuildSketch(handlebar_side_loc) as handlebar_side_conn_2:
    with BuildLine() as handlebar_side_conn_2_line:
        Polyline(
            (0, 0),
            (handlebar_size[0], 0),
            (handlebar_size[0], handlebar_size[1]),
            (0, handlebar_size[1]),
            close=True)
    make_face()

with BuildPart() as handlebar_side_conn:  # TODO: Add separately after exporting due to bugs?
    conn_base_faces = sum(
        stem_and_handle_bars_part.faces().group_by(Axis.Y)[-1:], ShapeList())
    conn_compound = Compound.make_compound(conn_base_faces)
    face_loc = Location(conn_base_faces.faces().filter_by(
        Axis.Y).face().vertices().group_by(Axis.X)[0].group_by(Axis.Z)[0].vertex().center())
    with BuildLine() as handlebar_side_conn_path:
        Spline(face_loc.position + (20, 0, 2),
               handlebar_side_loc.position + (0, 5, 0),
               tangents=[(0, 1, 0), (1, 0, 0)],
               tangent_scalars=[1, 1])
    sweep(sections=[handlebar_side_conn_2.sketch, conn_compound],
          path=handlebar_side_conn_path, multisection=True)

# Can't even mirror this buggy object, more post-processing...
# handlebar_side_conn_mirror = mirror(handlebar_side_conn)

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# %%
