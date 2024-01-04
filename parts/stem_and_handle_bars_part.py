# %%
from contextlib import suppress
from build123d import *
try:
    from global_params import *
    from headset_screw_part import headset_screw_part
except ImportError:  # HACK...
    from parts.global_params import *
    from parts.headset_screw_part import headset_screw_part
with suppress(ImportError):  # Optional
    import ocp_vscode

# ================== PARAMETERS ==================

# Measurements...
stem_rect = (35, 35)  # Stem "rectangle" (horizontal, vertical)
# Where to connect to the stem from the center of the circle
stem_range = (20, 45)
stem_fillet = 5.0  # Fillet radius of the stem (square -> circle)
# How much to overlap the stem with our model for a stronger connection
stem_clip = (stem_fillet, 2.0)

# ================== MODELLING ==================

conn_face = headset_screw_part.faces().group_by(Axis.X)[-1]
conn_face_center = conn_face.face().center()
conn_face_bb = conn_face.face().bounding_box()
with BuildSketch() as sweep_obj:
    # add(conn_face)
    Rectangle(3, 10)
    # with BuildLine() as sweep_obj_line:
    #     Polyline(conn_face_bb.min, (conn_face_bb.min.X, conn_face_bb.max.Y, conn_face_bb.min.Z),
    #              conn_face_bb.max, (conn_face_bb.min.X, conn_face_bb.min.Y, conn_face_bb.max.Z), close=True)
    # make_face()
with BuildLine() as sweep_path:
    Line((conn_face_center.Z, 0, 0), (conn_face_center.Z, 0, 10))

stem_and_handle_bars_part = sweep(sections=sweep_obj, path=sweep_path)


if __name__ == "__main__":  # While developing this single part
    ocp_vscode.show_all()

# %%
