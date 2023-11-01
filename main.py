import cadquery as cq
from cq_warehouse.drafting import Draft

# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended width for most walls of this print
eps = 1e-5  # A small number

# Bike measurements
stem_screw_diameter = 4.0  # Diameter of the screw that connects the stem to the fork
stem_circle_flat_radius = 10.0  # Radius of the flat part of the circle
stem_circle_radius = 15  # Radius of the circle
stem_circle_max_height = 3.0  # Maximum height of the circle
stem_rect = (35, 35)  # Stem "rectangle"
stem_range = (20, 45)  # Where to connect to the stem from the center of the circle
stem_fillet = 5.0  # Fillet radius of the stem (square -> circle)

# Create drawing instance with appropriate settings
draft = Draft(font_size=3)

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
    .circle(stem_screw_diameter / 2)  # To remove the screw hole
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

# Add stem rect limits
obj += (
    cq.Workplane("XY", origin=(stem_range[1], 0, wall))  # HACK: Force to split the edge
    .rect(-(stem_range[1] - stem_range[0]), stem_rect[1], centered=(False, True))
    .extrude(-wall)
    .pushPoints([(0, (stem_rect[1] + wall) / 2), (0, -(stem_rect[1] + wall) / 2)])
    .rect(-(stem_range[1] - stem_range[0]), wall, centered=(False, True))
    .extrude(-stem_rect[0])
    # Inner cantilever
    .faces("<Z")
    .each(lambda f: cq.Workplane(f).rect((stem_range[1] - stem_range[0]),
                                         (wall/1.999 + stem_fillet) * (1 if f.BoundingBox().ymin < 0 else -1),
                                         centered=(True, False)).extrude(wall).val())
)
# Stem fillet
obj = (
    obj.faces("|Y").faces(">>Y[1] or <<Y[1]").faces(">X").edges(">Z or <Z").fillet(stem_fillet)
    .edges(">Y or <Y").edges(">Z or <Z").fillet(wall)
)

#
show_object(obj)
