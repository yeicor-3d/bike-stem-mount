# %%
from contextlib import suppress
from build123d import *
from copy import copy, deepcopy
import math
try:
    from global_params import *
    from headset_screw import headset_screw_part, stem_circle_max_height, stem_circle_radius
    from screwable_cylinder import ScrewableCylinder
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.headset_screw import headset_screw_part, stem_circle_max_height, stem_circle_radius
    from parts.screwable_cylinder import ScrewableCylinder
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

smoothing_offset = 0.5
stem_part = sweep(sections=[
    sweep_obj,
    sweep_obj.sketch.moved(Location((0, 0, smoothing_offset))),
    sweep_obj_2.sketch.moved(Location((0, 0, -smoothing_offset))),
    sweep_obj_2.sketch], path=sweep_path, multisection=True)
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
face = (stem_part.faces() >> Axis.X).face()
# NOTE: Backwards and unaligned due to eps (required non-coincident edge and axis)
rev_axis = Axis(face.edges().group_by(Axis.Z)
                [-1].edge().center()+(0, 0, eps), (0, 1, 0))
rev_to_align = revolve(profiles=face, axis=rev_axis, revolution_arc=stem_angle)
del face
rev_to_align = rev_to_align.rotate(rev_axis, -stem_angle)
del rev_axis
stem_part += rev_to_align
del rev_to_align
assert len(stem_part.solids()) == 1, "Expected 1 solid"
to_extrude = stem_part.faces().group_by(Axis.X)[-2]  # Why -1?
stem_part += extrude(to_extrude, amount=extrude_dir.length,
                     dir=extrude_dir.normalized())
# del extrude_dir
del stem_dist

# This export is required for handle_bars.py
stem_side_faces = split(stem_part, bisect_by=Plane(to_extrude.face())).faces()
del to_extrude
stem_side_faces = stem_side_faces.group_by(Axis.Y)[0] + \
    stem_side_faces.group_by(Axis.Y)[-1]
assert len(stem_side_faces) == 2, "Expected 2 side faces"

# Now add the stem connector (sides)
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

# Now add the stem connector (bottom)
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
to_fillet = stem_part.edges().filter_by(Axis((0, 0, 0), extrude_dir))
to_fillet -= to_fillet.group_by(Axis.Y)[0]  # Remove out
to_fillet -= to_fillet.group_by(Axis.Y)[-1]  # Remove out
assert len(
    to_fillet) == 4, "Unexpected number of edges to fillet for stem (in-only)"
stem_part = fillet(to_fillet, stem_fillet)
to_fillet = stem_part.edges().filter_by(
    Axis((0, 0, 0), extrude_dir)).group_by(Axis.Z)[0]
assert len(
    to_fillet) == 2, "Unexpected number of edges to fillet for stem (out-bottom)"
stem_part = fillet(to_fillet, stem_fillet)
del to_fillet
del extrude_dir

# Add joint
RigidJoint("front", stem_part, Location(stem_part.faces().group_by(
    Axis.Y)[0].face().center(), (0, -stem_angle, 0)))
RigidJoint("back", stem_part, -Location(stem_part.faces().group_by(
    Axis.Y)[-1].face().center(), (0, -stem_angle+180, 0)))

# Screw holes and part splitting
with BuildPart() as stem_screw_holes:
    tmp = ScrewableCylinder(rotation=(0, 180, 90))
    bb = tmp.bounding_box()
    sketch_loc = stem_part.location * \
        stem_part.joints["front"].relative_location * Plane.XZ.location
    with BuildSketch(Plane.XZ * Location((0, 0, bb.min.Y))):
        Rectangle(bb.size.X, bb.size.Z)
    del sketch_loc
    del bb
    extrude(until=Until.NEXT, target=tmp)
    del tmp
    # # HACK: To fix only half extrusion done due to contact between the two parts
    mirror(about=Plane.YZ)
    RigidJoint("center", stem_screw_holes.part, Location(
        stem_screw_holes.faces().group_by(Axis.Y)[-1].face().center()))
    stem_part.joints["front"].connect_to(
        stem_screw_holes.part.joints["center"])
    stem_screw_holes_mirror = deepcopy(stem_screw_holes.part)
    stem_part.joints["back"].connect_to(
        stem_screw_holes_mirror.joints["center"])
stem_part += stem_screw_holes.part
stem_part += stem_screw_holes_mirror
del stem_screw_holes
del stem_screw_holes_mirror

# Final split
RigidJoint("split_joint", stem_part, Location(stem_part.center() + (0, 0, 1), stem_part.faces(
).group_by(Axis.Z)[0].face().center_location.orientation))  # "Center" of screw hole
bb = stem_part.bounding_box()
cutout = Box(bb.size.X + tol, bb.size.Y + tol, screw_floating_cut)
RigidJoint("center", cutout, Location((0, 0, 0)))
stem_part.joints["split_joint"].connect_to(cutout.joints["center"])
stem_part -= cutout
del cutout

if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all(render_joints=True)
    # ocp_vscode.show(handlebar_side_conn_2, "handlebar_side_conn_2")

# %%
