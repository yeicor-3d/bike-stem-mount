# %%
from bike_stem_mount.parts.headset_screw import headset_screw_part
from bike_stem_mount.parts.stem import stem_part
from bike_stem_mount.parts.handle_bars import handle_bars_part
from bike_stem_mount.parts.global_params import *
from build123d import *

# ================== MODELLING (ASSEMBLY) ==================

with BuildPart() as assembly:
    add(headset_screw_part)
    add(stem_part)
assembly = assembly.part.fuse(handle_bars_part)  # HACK: Avoids crash ¯\_(ツ)_/¯
del headset_screw_part
del stem_part
del handle_bars_part

if len(assembly.solids()) != 4:
    print("Warning: Expected 4 solids, got %d" % len(assembly.solids()))

if __name__ == "__main__":
    try:
        import ocp_vscode
        ocp_vscode.show_all(render_joints=True)
    except ImportError:  # Optional
        pass

# %%

# ================== SHOWING/EXPORTING ==================

if __name__ == "__main__":
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
        assembly.export_stl("bike-stem-mount.stl")

# %%
