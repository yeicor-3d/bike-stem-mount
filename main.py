# %%
from parts.headset_screw import headset_screw_part
from parts.stem import stem_part
from parts.handle_bars import handle_bars_part
from parts.global_params import *
from contextlib import suppress
from build123d import *
from copy import deepcopy
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== MODELLING (ASSEMBLY) ==================

headset_screw = deepcopy(headset_screw_part.part)
stem = deepcopy(stem_part)
handle_bars = deepcopy(handle_bars_part.part)
del headset_screw_part
del stem_part
del handle_bars_part
RigidJoint("joint", headset_screw, Location(
    headset_screw.faces().group_by(Axis.X)[-1].face().center_location.position))
stem_headset_joint_loc = stem.faces().group_by(Axis.X)[
    0].face().center_location
stem_headset_joint_loc.orientation = (
    stem_headset_joint_loc.orientation.X, stem_headset_joint_loc.orientation.Y+90, stem_headset_joint_loc.orientation.Z)
RigidJoint("joint", stem, stem_headset_joint_loc)
del stem_headset_joint_loc
headset_screw.joints["joint"].connect_to(stem.joints["joint"])

assembly = headset_screw + stem + handle_bars
del headset_screw
del stem
del handle_bars

print("Assembly is valid: %s. Using solids: %s" %
      (assembly.is_valid(), assembly.solids()))

if 'ocp_vscode' in locals():
    with suppress(Exception):
        ocp_vscode.show_all(render_joints=True)

# %%

# ================== SHOWING/EXPORTING ==================

export = True
try:
    if "show_object" in locals():
        show_object(assembly, "bike-stem-mount")  # type: ignore
        export = False
    elif "ocp_vscode" in locals():
        ocp_vscode.show_all(render_joints=True)
        export = False
except Exception as ex:
    print("Cannot show model, exporting to STL instead (%s)" % ex)

if export:
    print("Exporting to STL")
    assembly.part.export_stl("bike-stem-mount.stl")

# %%
