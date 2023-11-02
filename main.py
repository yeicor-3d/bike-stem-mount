import os

import cadquery as cq
from cq_warehouse.drafting import Draft

# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended width for most walls of this print
eps = 1e-5  # A small number

# Bike measurements
stem_screw_radius = 2.0  # Diameter of the screw that connects the stem to the fork
stem_circle_flat_radius = 10.0  # Radius of the flat part of the circle
stem_circle_radius = 16  # Radius of the circle
stem_circle_max_height = 3.0  # Maximum height of the circle
stem_rect = (35, 35)  # Stem "rectangle"
stem_range = (20, 45)  # Where to connect to the stem from the center of the circle
stem_fillet = 5.0  # Fillet radius of the stem (square -> circle)
stem_clip = (stem_fillet, 2.0)  # How much to overlap the stem with our model for a stronger connection

# Create drawing instance with appropriate settings
draft = Draft(font_size=2.5)
draft_z = Draft(font_size=2.5, label_normal=(1, 0, 0))

# ================== MODELLING ==================

stem_circle_to_rect = stem_rect[0] / 2 - stem_circle_radius

# Generate basic 2D outline and extrude it
obj = (
    cq.Workplane("XY")
    .moveTo(-stem_circle_radius, 0)
    .radiusArc((0, stem_circle_radius), stem_circle_radius)
    .radiusArc((stem_circle_to_rect, stem_circle_radius + stem_circle_to_rect), stem_circle_to_rect)
    .hLine(stem_range[1] - stem_circle_to_rect)
    # .radiusArc((stem_range[1], stem_rect[1]/2 - max_fillet), max_fillet)
    .vLine(-stem_rect[1] / 2)
    .mirrorX()
    .extrude(wall)
    .moveTo(0, 0)
    # Remove the screw hole
    .circle(stem_screw_radius)  # To remove the screw hole
    .cutThruAll()
)

# Avoid the lip of the stem circle
stem_circle_forbidden = (
    cq.Workplane("XY")
    .circle(stem_circle_radius).circle(stem_circle_flat_radius)
    .extrude(stem_circle_max_height)
)
obj += stem_circle_forbidden.faces("<Z").shell(wall)
obj -= stem_circle_forbidden
stem_circle_forbidden = None

# Add stem rect limits
obj += (
    cq.Workplane("XY", origin=(stem_range[1], 0, wall))  # HACK: Force to split the edge
    .rect(-(stem_range[1] - stem_range[0]), stem_rect[1], centered=(False, True))
    .extrude(-wall)
    .pushPoints([(0, (stem_rect[1] + wall) / 2), (0, -(stem_rect[1] + wall) / 2)])
    .rect(-(stem_range[1] - stem_range[0]), wall, centered=(False, True))
    .extrude(-(stem_rect[0] + wall * 2))
)
# Inner cantilever
for f in obj.faces("|Y").faces(">>Y[1] or <<Y[1]").faces(">X").vals():
    bb = f.BoundingBox()
    newObj = (
        cq.Workplane("XZ", (bb.xmin, bb.ymin, bb.zmin))
        .rect(stem_range[1] - stem_range[0], stem_clip[0], centered=False)
        .extrude(stem_clip[1] * (-1 if bb.ymin < 0 else 1))
        .faces(">Y" if bb.ymin < 0 else "<Y").edges("|X"))
    newObj = newObj.chamfer(stem_clip[1] - eps, stem_clip[0] / 4)
    newObj = newObj.edges(">Y" if bb.ymin < 0 else "<Y").edges("|X").fillet(stem_clip[0] / 4 - eps)
    obj += newObj
    newObj = None

# Stem fillet
obj = (
    obj.faces("|Y").faces(">>Y[1] or <<Y[1]").faces(">X").edges(">Z").fillet(stem_fillet)
    .edges(">Y or <Y").edges(">Z or <Z").fillet(wall)
)

# Show main parameters in the model (for debugging, as it reduces performance)
if os.getenv('cq_draft'):
    drafts = cq.Assembly(None)
    draft_dist = 3 * wall
    draft_line = draft.font_size * 1.5
    drafts.add(draft.extension_line([(-stem_screw_radius, 0, 0), (0, 0, 0)], stem_rect[1] / 2 + draft_dist,
                                    "stem_screw_radius"))
    drafts.add(draft.extension_line([(-stem_circle_flat_radius, 0, 0), (0, 0, 0)],
                                    stem_rect[1] / 2 + draft_dist + draft_line, "stem_circle_flat_radius"))
    drafts.add(draft.extension_line([(-stem_circle_radius, 0, 0), (0, 0, 0)],
                                    stem_rect[1] / 2 + draft_dist + draft_line * 2, "stem_circle_radius"))
    drafts.add(
        draft_z.extension_line([(-stem_circle_radius, 0, 0), (-stem_circle_radius, 0, stem_circle_max_height)],
                               draft_dist, "stem_circle_max_height"))
    drafts.add(
        draft.extension_line([(-stem_circle_radius - wall, 0, 0), (-stem_circle_radius, 0, 0)],
                             stem_rect[1] / 2 + draft_dist + draft_line * 3, "wall"))
    drafts.add(
        draft.extension_line([(0, 0, 0), (stem_range[0], 0, 0)],
                             -(stem_rect[1] / 2 + draft_dist),
                             "stem_range[0]"))
    drafts.add(
        draft.extension_line([(0, 0, 0), (stem_range[1], 0, 0)],
                             -(stem_rect[1] / 2 + draft_dist + draft_line),
                             "stem_range[1]"))
    drafts.add(
        draft_z.extension_line([(stem_range[1], -stem_rect[1] / 2, 0), (stem_range[1], stem_rect[1] / 2, 0)],
                               draft_dist, "stem_rect[1]"))
    drafts.add(
        draft_z.extension_line(
            obj.faces(">X").edges("not |Y").edges("<<Z[1]").val(),
            draft_dist + draft_line, "stem_fillet"))
    drafts.add(
        draft_z.extension_line(
            [(stem_range[1], -stem_rect[1] / 2, 0), (stem_range[1], -stem_rect[1] / 2, -stem_rect[0])],
            -draft_dist, "stem_rect[0]"))
    drafts.add(
        draft_z.extension_line(
            [(stem_range[1], -stem_rect[1] / 2, -stem_rect[0] - wall + stem_clip[0]),
             (stem_range[1], -stem_rect[1] / 2, -stem_rect[0] - wall)],
            -draft_dist, "stem_clip[0]"))
    drafts.add(
        draft.extension_line(
            [(stem_range[1], -stem_rect[1] / 2, -stem_rect[0] - wall + stem_clip[0] / 2),
             (stem_range[1], -stem_rect[1] / 2 + stem_clip[1], -stem_rect[0] - wall + stem_clip[0] / 2)],
            -draft_dist, "stem_clip[1]"))
    show_object(drafts, "drafts")

    # Show the model
    show_object(obj, "obj")
