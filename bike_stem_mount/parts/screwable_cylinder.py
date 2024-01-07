# %%
from dataclasses import dataclass
from typing import Union
from build123d import *
from math import *
from bike_stem_mount.parts.global_params import *

# ================== MODELLING ==================


@dataclass
class ScrewableCylinder(BasePartObject):
    screw_length: float = 8
    screw_diameter: float = 5  # M5
    screw_head_diameter: float = 8.5  # M5
    screw_head_height: float = 5  # M5
    nut_inscribed_diameter: float = 7  # M5
    nut_height: float = 2.7  # M5
    wall_size: float = wall
    round: bool = False
    rotation: RotationLike = (0, 0, 0)
    align: Union[Align, tuple[Align, Align, Align]] = None
    mode: Mode = Mode.ADD

    def __post_init__(self):
        with BuildPart() as part:
            total_height = self.screw_length + self.screw_head_height
            max_hole_diameter = max(
                self.screw_diameter + 2*tol, self.screw_head_diameter + 2*tol,
                (self.nut_inscribed_diameter + 2*tol) / cos(radians(360/6/2)))
            # Core
            Cylinder(max_hole_diameter/2 + self.wall_size, total_height)
            if self.round:
                fillet(edges(), radius=self.wall_size)
            # Top hole
            with BuildSketch(faces() >> Axis.Z):
                Circle(self.screw_head_diameter/2 + tol)
            extrude(amount=-self.screw_head_height, mode=Mode.SUBTRACT)
            # Screw hole
            Cylinder(self.screw_diameter/2 + tol,
                     self.screw_length, mode=Mode.SUBTRACT)
            # Nut hole
            with BuildSketch(faces() << Axis.Z):
                RegularPolygon(self.nut_inscribed_diameter/2 +
                               tol, 6, major_radius=False)
            extrude(amount=-self.nut_height, mode=Mode.SUBTRACT)
        super().__init__(part=part.part, rotation=self.rotation,
                         align=self.align, mode=self.mode)


if __name__ == "__main__":
    import ocp_vscode
    part = ScrewableCylinder(rotation=(0, 0, 90))
    ocp_vscode.show_all(render_joints=True)
