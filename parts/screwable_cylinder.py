# %%
from contextlib import suppress
from typing import Union
from build123d import *
try:
    from global_params import *
except ImportError:  # HACK...
    from parts.global_params import *
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== MODELLING ==================


class ScrewableCylinder(BasePartObject):
    def __init__(
        self,
        screw_length: float = 8,
        screw_diameter: float = 5,  # M5
        screw_head_diameter: float = 8.5,  # M5
        screw_head_height: float = 5,  # M5
        nut_inscribed_diameter: float = 7,  # M5
        nut_height: float = 2.7,  # M5
        rotation: RotationLike = (0, 0, 0),
        align: Union[Align, tuple[Align, Align, Align]] = None,
        mode: Mode = Mode.ADD,
    ):
        with BuildPart() as part:
            total_height = screw_length + screw_head_height + 2*tol
            max_hole_diameter = max(
                screw_diameter, screw_head_diameter, nut_inscribed_diameter)
            # Core
            Cylinder(max_hole_diameter/2 + wall + tol, total_height)
            # Top hole
            with BuildSketch(faces() >> Axis.Z):
                Circle(screw_head_diameter/2 + tol)
            extrude(amount=-screw_head_height, mode=Mode.SUBTRACT)
            # Screw hole
            Cylinder(screw_diameter/2 + tol, screw_length, mode=Mode.SUBTRACT)
            # Nut hole
            with BuildSketch(faces() << Axis.Z):
                RegularPolygon(nut_inscribed_diameter/2 +
                               tol, 6, major_radius=False)
            extrude(amount=-nut_height, mode=Mode.SUBTRACT)
        super().__init__(part=part.part, rotation=rotation, align=align, mode=mode)
        # NOTE: Create the joint after applying alingment + rotation
        RigidJoint("edge_center", self, Location((self.location * Location(part.edges().filter_by(
            Axis.Z).group_by(SortBy.LENGTH)[-1].edge().center())).position))


if __name__ == "__main__":
    part = ScrewableCylinder(rotation=(0, 0, 90))
    ocp_vscode.show_all(render_joints=True)
