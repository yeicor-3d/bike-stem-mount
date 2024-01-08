# %%
from dataclasses import dataclass
from build123d import *
from copy import copy, deepcopy
import math
from bike_stem_mount.parts.global_params import *
from bike_stem_mount.parts.headset_screw import headset_screw_part, p as headset_p
from bike_stem_mount.parts.screwable_cylinder import ScrewableCylinder

# ================== PARAMETERS ==================


@dataclass
class StemParams:
    angle: float = -9
    """Angle from the headset to the stem (ignoring right angle)"""
    range: tuple[float, float] = (20, 45)
    """Range of the stem walls (from the headset center)"""
    width: float = 35
    """Width of the stem (horizontal)"""
    height: float = 35
    """Height of the stem (vertical)"""
    fillet: float = 4.75


p = StemParams()


# ================== MODELLING ==================

conn_face = headset_screw_part.faces().group_by(Axis.X)[-1].face()
del headset_screw_part
sweep_obj = conn_face.transformed(
    rotate=(0, -90, 0), offset=(0, 0, -conn_face.center().X))

with BuildSketch(Plane.XY.offset(p.range[0]-headset_p.circle_radius)) as sweep_obj_2:
    Rectangle(wall, p.width + 2 * wall,
              align=(Align.MAX, Align.CENTER))

with BuildLine() as sweep_path:
    Line((0, 0, 0), (0, 0, p.range[0]-headset_p.circle_radius))

smoothing_offset = 0.5
stem_part = sweep(sections=[
    sweep_obj,
    sweep_obj.moved(Location((0, 0, smoothing_offset))),
    sweep_obj_2.sketch.moved(Location((0, 0, -smoothing_offset))),
    sweep_obj_2.sketch], path=sweep_path, multisection=True)
assert stem_part.is_valid(), "Sweep failed"
conn_face_loc = copy(conn_face.center_location)
stem_part = stem_part.moved(
    Location(conn_face_loc.position - (0, 0, conn_face.bounding_box().size.Z/2), (0, 90, 0)))
# del sweep_obj
del sweep_path
del conn_face_loc
del conn_face
del sweep_obj

stem_dist = p.range[1] - p.range[0]
stem_height = stem_dist * math.tan(math.radians(p.angle))
extrude_dir = Vector(stem_dist, 0, stem_height)
face = (stem_part.faces() >> Axis.X).face()
# NOTE: Backwards and unaligned due to eps (required non-coincident edge and axis)
rev_axis = Axis(face.edges().group_by(
    Axis.Z)[0].group_by(Axis.Y)[0].edge().center()-(0, 0, eps), (0, 1, 0))
rev_to_align = revolve(profiles=face, axis=rev_axis,
                       revolution_arc=abs(p.angle))
del face, rev_axis
stem_part += rev_to_align
del rev_to_align
assert len(stem_part.solids()) == 1, "Expected 1 solid"
to_extrude = stem_part.faces().group_by(Axis.X)[-2]  # Why -1?
stem_part += extrude(to_extrude, amount=extrude_dir.length,
                     dir=extrude_dir.normalized())
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
        with BuildSketch(Location(edge@0.5, (0, -p.angle, 0))):
            Rectangle((edge@1 - edge@0).length, wall,
                      align=(Align.CENTER, Align.MAX if is_far else Align.MIN))
        extrude(amount=-(p.height + 2 * wall),
                dir=Vector(-math.sin(math.radians(p.angle)), 0, math.cos(math.radians(p.angle))))
    stem_part += side_extrusion.part
    del side_extrusion
del top_edges
del edge

# Now add the stem connector (bottom)
with BuildPart() as bottom_extrusion:
    bottom_close = stem_part.faces().group_by(
        Axis.Z)[0].edges().group_by(Axis.Y)[0].edge()
    with BuildSketch(Location(bottom_close@0.5, (90, 0, p.angle))):
        Rectangle((bottom_close@1 - bottom_close@0).length,
                  wall, align=(Align.CENTER, Align.MIN))
    extrude(amount=-(p.height + 2 * wall))
stem_part += bottom_extrusion.part
del bottom_extrusion
del bottom_close

# Add joint
RigidJoint("front", stem_part, Location(stem_part.faces().group_by(
    Axis.Y)[0].face().center(), (0, -p.angle, 0)))
RigidJoint("back", stem_part, -Location(stem_part.faces().group_by(
    Axis.Y)[-1].face().center(), (0, -p.angle+180, 0)))

# Screw holes and part splitting
with BuildPart() as stem_screw_holes:
    cyl = ScrewableCylinder(rotation=(0, 180, 90))
    bb = cyl.bounding_box()
    sketch_loc = stem_part.location * \
        stem_part.joints["front"].relative_location * Plane.XZ.location
    with BuildSketch(Plane.XZ * Location((0, 0, bb.min.Y))):
        Rectangle(bb.size.X, bb.size.Z)
    del sketch_loc
    extrude(until=Until.NEXT, target=cyl)
    # # HACK: To fix only half extrusion done due to contact between the two parts
    mirror(about=Plane.YZ)
    center_loc = faces().group_by(Axis.Y)[-1].face().center()
    # Make TOP AND BOTTOM more 3D print friendly with inbuilt supports
    for face in [faces().group_by(Axis.Z)[-1].face(), faces().group_by(Axis.Z)[0].face()]:
        is_top = face.center().Z > 0
        # - Part 1: extrude top to convert to incline
        max_extrude = p.height / 2 + wall + \
            (0 if is_top else -p.fillet/2)  # Approx
        extrude(face, amount=max_extrude)
        # - Part 2: Cut the top using a plane
        tmp = vertices().group_by(
            Axis.Z)[-1 if is_top else 0].group_by(Axis.Y)[-1].group_by(Axis.X)[-1].vertex().center()
        tmp.Z = max_extrude * (1 if is_top else -1)
        offset_z = tmp.Z - \
            ((bb.max.Z - cyl.nut_height)
             if is_top else (bb.min.Z))
        offset_y = tmp.Y - bb.min.Y
        cut_angle = math.degrees(math.atan2(offset_z, offset_y))
        # print(f"Cut angle: {cut_angle}")
        assert abs(cut_angle) > 40, "<50 degree overhangs required"
        cut_plane = Plane(Location(tmp.center(), (cut_angle, 0, 0)))
        split(bisect_by=cut_plane, keep=Keep.BOTTOM if is_top else Keep.TOP)
        del face, cut_plane, tmp
    del bb, cyl
    # Fillet
    to_fillet = stem_screw_holes.faces().group_by(Axis.Z)[0].edges()
    to_fillet += stem_screw_holes.faces().group_by(Axis.Z)[-1].edges()
    to_fillet -= to_fillet.group_by(SortBy.LENGTH)[0]
    to_fillet -= to_fillet.group_by(SortBy.LENGTH)[0]
    to_fillet -= to_fillet.group_by(Axis.Y)[-1]
    to_fillet -= to_fillet.group_by(SortBy.LENGTH)[-1]
    fillet(to_fillet, radius=wall)
    del to_fillet
RigidJoint("center", stem_screw_holes.part, Location(center_loc))
del center_loc
stem_part.joints["front"].connect_to(
    stem_screw_holes.part.joints["center"])
stem_screw_holes_mirror = deepcopy(stem_screw_holes.part)
stem_part.joints["back"].connect_to(
    stem_screw_holes_mirror.joints["center"])
stem_part += stem_screw_holes.part
stem_part += stem_screw_holes_mirror
del stem_screw_holes
del stem_screw_holes_mirror

# Stem fillet
to_fillet = stem_part.edges().filter_by(Axis((0, 0, 0), extrude_dir))
to_fillet -= to_fillet.group_by(Axis.Y)[0]  # Remove out
to_fillet -= to_fillet.group_by(Axis.Y)[-1]  # Remove out
assert len(
    to_fillet) == 4, "Unexpected number of edges to fillet for stem (in-only)"
stem_part = fillet(to_fillet, p.fillet)
to_fillet = stem_part.edges().filter_by(
    Axis((0, 0, 0), extrude_dir)).group_by(Axis.Z)[0]
assert len(
    to_fillet) == 2, "Unexpected number of edges to fillet for stem (out-bottom)"
# Not as necessary, and improves printability
stem_part = fillet(to_fillet, p.fillet/2)
del to_fillet
del extrude_dir

# # Final fillet
to_fillet = stem_part.faces().group_by(Axis.X)[-1].edges()
stem_part = stem_part.fillet(radius=wall/2.01, edge_list=to_fillet)
del to_fillet

# Final split
RigidJoint("split_joint", stem_part, Location(
    stem_part.center(), (0, -p.angle, 0)))
bb = stem_part.bounding_box()
cutout = Box(bb.size.X + tol, bb.size.Y + tol, screw_floating_cut)
RigidJoint("center", cutout, Location((0, 0, 0)))
stem_part.joints["split_joint"].connect_to(cutout.joints["center"])
stem_part -= cutout
del cutout

if __name__ == "__main__":  # While developing this single part
    import ocp_vscode
    ocp_vscode.show_all(measure_tools=True, render_joints=True,
                        reset_camera=ocp_vscode.Camera.CENTER)
