# %%
from contextlib import suppress
from build123d import *
from copy import copy, deepcopy
import math
try:
    from global_params import *
    from headset_screw import headset_screw_part, stem_circle_max_height, stem_circle_radius
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.headset_screw import headset_screw_part, stem_circle_max_height, stem_circle_radius
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== PARAMETERS ==================

stem_angle = 20  # Stem angle wrt the headset
stem_rect = (35, 35)  # Stem "rectangle" (horizontal, vertical)
# Where to connect to the stem from the center of the circle
stem_range = (20, 45)
stem_fillet = 4.75  # Fillet radius of the stem (square -> circle)
# How much to overlap the stem with our model for a stronger connection
stem_clip = (stem_fillet, 2.0)

# ================== MODELLING ==================

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

with BuildSketch(Plane.XY.offset(stem_range[0]-stem_circle_radius)) as sweep_obj_2:
    Rectangle(wall, stem_rect[0] + 2 * wall,
              align=(Align.MIN, Align.CENTER))

with BuildLine() as sweep_path:
    Line((0, 0, 0), (0, 0, stem_range[0]-stem_circle_radius))

stem_part = sweep(sections=[sweep_obj, sweep_obj.sketch.moved(Location((0, 0, 1))), sweep_obj_2.sketch],
                  path=sweep_path, multisection=True)
assert stem_part.is_valid(), "Sweep failed"
conn_face_loc = copy(conn_face.center_location)
stem_part = stem_part.moved(
    Location(conn_face_loc.position - (0, 0, conn_face_bb.size.Z/2), (180, 90, 0)))
# del sweep_obj
del sweep_path
del conn_face_loc
del conn_face
del conn_face_bb
del sweep_obj

stem_dist = stem_range[1] - stem_range[0]
stem_height = stem_dist * math.tan(math.radians(stem_angle))
extrude_dir = Vector(stem_dist, 0, stem_height)
to_extrude = stem_part.faces().group_by(Axis.X)[-1]
stem_part += extrude(to_extrude, amount=extrude_dir.length,
                     dir=extrude_dir.normalized())
del to_extrude
del extrude_dir
del stem_dist
to_fillet = stem_part.edges().filter_by(
    lambda e: abs((e@0 - e@1).X) < eps).group_by(Axis.X)[1]
stem_part = fillet(to_fillet, 1.9)
del to_fillet

# This export is required for handle_bars.py
stem_side_faces = stem_part.faces().filter_by(
    lambda f: abs(f.normal_at((0, 0)).Y) > 1-eps)
assert len(stem_side_faces) == 2, "Expected 2 side faces"

# Now add the stem connector (part 1)
top_edges = stem_side_faces.edges().group_by(SortBy.LENGTH)[-1]
for edge in top_edges:
    is_far = (edge@0).Y > 0
    with BuildPart() as side_extrusion:
        with BuildSketch(Location(edge@0.5, (0, -stem_angle, 0))):
            Rectangle((edge@1 - edge@0).length, wall,
                      align=(Align.CENTER, Align.MAX if is_far else Align.MIN))
        extrude(amount=-(stem_rect[1] + 2 * wall),
                dir=Vector(-math.sin(math.radians(stem_angle)), 0, math.cos(math.radians(stem_angle))))
    stem_part += side_extrusion.part
    del side_extrusion
del top_edges
del edge

# Now add the stem connector (part 2)
with BuildPart() as bottom_extrusion:
    bottom_close = stem_part.faces().group_by(
        Axis.Z)[0].edges().group_by(Axis.Y)[0].edge()
    with BuildSketch(Location(bottom_close@0.5, (90, 0, stem_angle))):
        Rectangle((bottom_close@1 - bottom_close@0).length,
                  wall, align=(Align.CENTER, Align.MIN))
    extrude(amount=-(stem_rect[1] + 2 * wall))
stem_part += bottom_extrusion.part
del bottom_extrusion
del bottom_close

# Stem fillet
to_fillet = stem_part.edges().filter_by(Plane.XZ)
to_fillet = sum(to_fillet.group_by(SortBy.LENGTH)[-7:-5], ShapeList())
to_fillet = to_fillet.group_by(Axis.Z)[-1]
stem_part = fillet(to_fillet, 0.4)
to_fillet = stem_part.edges().filter_by(Plane.XZ)
to_fillet = sum(to_fillet.group_by(SortBy.LENGTH)[-11:-8], ShapeList())
to_fillet -= to_fillet.group_by(Axis.Y)[0]
to_fillet -= to_fillet.group_by(Axis.Y)[-1]
to_fillet -= to_fillet.group_by(Axis.Y)[-1]
assert len(
    to_fillet) == 4, "Unexpected number of edges to fillet (weak filtering...)"
stem_part = fillet(to_fillet, stem_fillet)
to_fillet = stem_part.edges().group_by(Axis.Z)[3]
assert len(to_fillet) == 2, "Unexpected number of edges to fillet"
stem_part = fillet(to_fillet, stem_fillet)
del to_fillet

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# %%
