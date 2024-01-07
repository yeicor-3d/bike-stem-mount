# %%
from dataclasses import dataclass
from build123d import *
from bike_stem_mount.parts.global_params import *
from bike_stem_mount.parts.stem import stem_height, stem_side_faces
from bike_stem_mount.parts.screwable_cylinder import ScrewableCylinder

# ================== PARAMETERS ==================


@dataclass
class HandleBarParams:
    offset_x_center: float = 80
    offset_y_start: float = 25
    width: float = 10
    height: float = wall
    rotation: float = 5
    radius: float = 16


p = HandleBarParams()

# ================== MODELLING ==================

handlebar_side_loc = Location(
    (p.offset_x_center, p.offset_y_start, stem_height), (0, 90, 90))
with BuildSketch(handlebar_side_loc) as handlebar_side:
    Rectangle(p.width, p.height,
              align=Align.MIN, rotation=-p.rotation)
with BuildPart() as handlebar_side_conn:
    face = stem_side_faces.group_by(Axis.Y)[-1].face()
    del stem_side_faces
    face_loc = Location(face.edges().group_by(
        SortBy.LENGTH)[-1].group_by(Axis.Z)[0].edge()@1)
    with BuildLine() as handlebar_side_conn_path:
        Spline(face_loc.position,
               handlebar_side_loc.position,
               tangents=[(0, 1, 0), Vector(1, 0, 0).normalized()],
               tangent_scalars=[.5, 1])
    thin_factor = 3
    sweep(sections=[handlebar_side.sketch, handlebar_side.sketch.moved(Location((-thin_factor, 0, 0))), face],
          path=handlebar_side_conn_path, multisection=True)
    del handlebar_side
    del face
    del face_loc
    del handlebar_side_conn_path
handlebar_side_conn = handlebar_side_conn.part

# Nice and clean filleting
to_fillet = handlebar_side_conn.faces().group_by(Axis.Y)[1].edges()
to_fillet += handlebar_side_conn.faces().group_by(Axis.Y)[-1].edges()
to_fillet -= to_fillet.group_by(SortBy.LENGTH)[0]
handlebar_side_conn = handlebar_side_conn.fillet(
    radius=wall/2.05, edge_list=to_fillet)

handle_bar_top_loc = handlebar_side_conn.faces().group_by(
    Axis.X)[-1].face().center_location
with BuildPart() as handle_bar_core:
    with BuildSketch(handle_bar_top_loc):
        RectangleRounded(p.height, p.width, p.height/2.01,
                         rotation=-p.rotation)
    revolve(axis=Axis(handle_bar_top_loc.position - (0, 0, p.radius +
                                                     p.height/2), (0, 1, 0)))
handle_bar_core = handle_bar_core.part

# Make adapter for screwable cylinder to connect to the ring
screwable_cylinder = ScrewableCylinder(rotation=(0, 180, 0))
bb = screwable_cylinder.bounding_box()
sc_box = Box(bb.size.X, bb.size.Y, bb.size.Z)
handle_bar_face_cut = handle_bar_core.faces().group_by(SortBy.AREA)[-1].face()
hbfc_com = handle_bar_face_cut.center(CenterOf.MASS)
handle_bar_face_cut = handle_bar_face_cut.moved(
    Location((-hbfc_com.X + p.radius, -hbfc_com.Y, -hbfc_com.Z))) & sc_box
# Push it in the X axis to touch the screwable cylinder's bounding box
handle_bar_face_cut = handle_bar_face_cut.moved(Location(Vector(10, 0, 0)))
handle_bar_face_cut = handle_bar_face_cut.moved(
    Location(Vector(-handle_bar_face_cut.face().distance_to(sc_box), 0, 0)))
sc_face_cut = screwable_cylinder.faces().group_by(
    SortBy.AREA)[-1].face() & sc_box.moved(Location((bb.size.X/2, 0, 0)))
screw_part_adapter_add = loft([handle_bar_face_cut, sc_face_cut])
assert screw_part_adapter_add.is_valid(), "Loft failed"
# HACK: Loft doesn't match precisely, so we fuse it with extremely high tolerance
screw_part_adapter = screwable_cylinder.fuse(
    screw_part_adapter_add, tol=1.0).clean()
del screwable_cylinder, sc_box, sc_face_cut, screw_part_adapter_add
to_fillet = screw_part_adapter.faces().group_by(Axis.Z)[-1].edges()
to_fillet += screw_part_adapter.faces().group_by(Axis.Z)[0].edges()
to_fillet -= to_fillet.group_by(SortBy.LENGTH)[0]
to_fillet -= to_fillet.group_by(SortBy.LENGTH)[-1]
to_fillet -= to_fillet.group_by(Axis.X)[-1]
screw_part_adapter = screw_part_adapter.fillet(wall-tol, to_fillet)
del to_fillet

handle_bar_center = handle_bar_core.center()

# Connect the adapter to the handlebar
spa_bb = screw_part_adapter.bounding_box()
screw_part_adapter = screw_part_adapter.located(handle_bar_face_cut.location.inverse(
) * Location((-hbfc_com.X + p.radius, -hbfc_com.Y, -hbfc_com.Z)).inverse())
del handlebar_side_loc, handle_bar_top_loc, handle_bar_face_cut, hbfc_com
# HACK: Loft doesn't match precisely, so we fuse it
handle_bar_core = handle_bar_core.fuse(screw_part_adapter)

# Connect the mirrored adapter, around the center of the handlebar
screw_part_adapter_mirror = mirror(objects=screw_part_adapter,
                                   about=Plane(Location(handle_bar_center) * Plane.YZ.location))
handle_bar_core = handle_bar_core.fuse(screw_part_adapter_mirror)
del screw_part_adapter, screw_part_adapter_mirror
assert len(handle_bar_core.solids()) == 1, "Expected 1 solid"

# Add the finished handle bar to the crazy side conn curve
handlebar_side_conn = handlebar_side_conn.fuse(handle_bar_core)
assert len(handlebar_side_conn.solids()) == 1, "Expected 1 solid"
del handle_bar_core

# Cut the handlebar side connector to fit the handlebar
RigidJoint("split_joint", handlebar_side_conn, Location(
    handle_bar_center + (0, 0, 1)))  # "Center" of screw hole
del handle_bar_center
bb = handlebar_side_conn.bounding_box()
cutout = Box(bb.size.X + tol, bb.size.Y + tol, screw_floating_cut)
RigidJoint("center", cutout, Location((0, 0, 0)))
handlebar_side_conn.joints["split_joint"].connect_to(cutout.joints["center"])
handlebar_side_conn = handlebar_side_conn.cut(cutout)
del cutout
assert len(handlebar_side_conn.solids()) == 2, "Expected 2 solids"

# Join a mirrored version of the handlebar side
handle_bars_part = handlebar_side_conn
handle_bars_part = handle_bars_part.fuse(
    mirror(objects=handlebar_side_conn))
del handlebar_side_conn

if __name__ == "__main__":  # While developing this single part
    import ocp_vscode
    ocp_vscode.show_all()
