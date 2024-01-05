# %%
from parts.headset_screw import headset_screw_part
from parts.stem import stem_part
from parts.handle_bars import handle_bars_part
from contextlib import suppress
from build123d import *
with suppress(ImportError):  # Optional
    import ocp_vscode

# %%
# ================== MODELLING (ASSEMBLY) ==================

with BuildPart() as assembly:
    add(headset_screw_part)
    add(stem_part)
    add(handle_bars_part)

if 'ocp_vscode' in locals():
    with suppress(Exception):
        ocp_vscode.show_all()

# %%

# ================== SHOWING/EXPORTING ==================

export = True
try:
    if "show_object" in locals():
        show_object(assembly, "bike-stem-mount")  # type: ignore
        export = False
    elif "ocp_vscode" in locals():
        ocp_vscode.reset_show()
        ocp_vscode.show_all()
        export = False
except Exception as ex:
    print("Cannot show model, exporting to STL instead (%s)" % ex)

if export:
    print("Exporting to STL")
    assembly.part.export_stl("bike-stem-mount.stl")

# %%
