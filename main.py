# %%
from parts.headset_screw_part import headset_screw_part
from parts.stem_and_handle_bars_part import stem_and_handle_bars_part
from contextlib import suppress
from build123d import *
with suppress(ImportError):  # Optional
    import ocp_vscode

# %%
# ================== MODELLING (ASSEMBLY) ==================

if 'ocp_vscode' in locals():
    with suppress(Exception):
        ocp_vscode.show_all()

# %%

# ================== SHOWING/EXPORTING ==================

export = True
try:
    if "show_object" in locals():
        show_object(headset_screw_part, "bike-stem-mount")  # type: ignore
        export = False
    elif "ocp_vscode" in locals():
        ocp_vscode.reset_show()
        ocp_vscode.show_all()
        export = False
except Exception as ex:
    print("Cannot show model, exporting to STL instead (%s)" % ex)

if export:
    print("Exporting to STL")
    headset_screw_part.part.export_stl("bike-stem-mount.stl")

# %%
