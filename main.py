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

with BuildPart() as assembly:
    add(headset_screw_part)
    add(stem_part)
    add(handle_bars_part)
del headset_screw_part
del stem_part
del handle_bars_part

assert len(assembly.solids()) == 4, \
    "Bad assembly, expected 4 solids (got %s)" % assembly.solids()

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
