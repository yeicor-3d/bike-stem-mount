# %%
from dataclasses import dataclass
from build123d import *
from bike_stem_mount.parts.global_params import *

# ================== PARAMETERS ==================


@dataclass
class HeadsetScrewParams:
    screw_radius: float = 2.0  # Diameter of the screw that connects the stem to the fork
    screw_flat_radius: float = 4.0  # Radius of the flat part of the screw
    circle_flat_radius: float = 10.0  # Radius of the flat part of the circle
    circle_radius: float = 16  # Radius of the circle
    circle_max_height: float = 3.0  # Maximum height of the circle


p = HeadsetScrewParams()

# ================== MODELLING ==================

with BuildPart() as headset_screw_part:
    def outer_wall(radius: float = p.circle_radius):
        with BuildSketch() as sk1:
            with BuildLine():  # top_face_outer_line
                arc = CenterArc((0, 0), radius, 180, -90)
                Polyline(arc@1, (radius, (arc@1).Y), (radius, 0))
                del arc
                mirror()
            make_face()
        return sk1

    # Core sketch and extrusion
    with BuildSketch():
        add(outer_wall())
        Circle(radius=p.screw_radius, mode=Mode.SUBTRACT)
    extrude(amount=p.circle_max_height + wall)

    # Remove a little extra material for the screw head
    with BuildSketch(Plane.XY.offset(wall)):
        Circle(radius=p.screw_flat_radius)
    extrude(amount=p.circle_max_height, mode=Mode.SUBTRACT)

    # Remove a little material for the outer wall of the headset
    with BuildSketch():
        add(outer_wall(radius=p.circle_flat_radius + wall))
        Circle(radius=p.circle_flat_radius, mode=Mode.SUBTRACT)
    extrude(amount=p.circle_max_height, mode=Mode.SUBTRACT)

    # Final chamfering
    to_chamfer = headset_screw_part.edges().filter_by(GeomType.CIRCLE).group_by(
        SortBy.LENGTH)[1].sort_by(Axis.Z)[-1]
    chamfer(to_chamfer, p.circle_max_height - eps)
    del to_chamfer
    to_chamfer = headset_screw_part.edges().filter_by(
        GeomType.CIRCLE).group_by(Axis.Z)[0]
    to_chamfer -= to_chamfer.group_by(SortBy.LENGTH)[0]
    to_chamfer -= to_chamfer.group_by(SortBy.LENGTH)[-2]
    to_chamfer += headset_screw_part.edges().group_by(Axis.Z)[0].group_by(
        Axis.X)[-2]
    chamfer(to_chamfer, p.circle_max_height - eps)
    del to_chamfer

    # Final filleting
    to_fillet = headset_screw_part.faces().group_by(Axis.Z)[-1].edges()
    to_fillet -= to_fillet.group_by(Axis.X)[-1]
    fillet(to_fillet, p.circle_max_height - wall)
    del to_fillet
    to_fillet = headset_screw_part.edges().group_by(
        Axis.Z)[0].group_by(SortBy.LENGTH)[-1]
    fillet(to_fillet, wall)
    del to_fillet

headset_screw_part = headset_screw_part.part

if __name__ == "__main__":  # While developing this single part
    import ocp_vscode
    ocp_vscode.show_all()
