"""Pure nominal energy and millimetre geometry models; no device operations."""

import math

_UNSET = object()


def checked(values, fields):
    if values is _UNSET:
        values = {}
    if not isinstance(values, dict) or set(values) - set(fields):
        raise ValueError("Use an object with only documented settings.")
    result = {}
    for key, (low, high, default) in fields.items():
        value = values.get(key, default)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not low <= value <= high
            or not math.isfinite(value)
        ):
            raise ValueError(f"{key} must be a finite number from {low} to {high}.")
        result[key] = value
    return result


def budget(values=_UNSET):
    settings = checked(
        values,
        {
            "capacity_wh": (1, 500, 74),
            "load_w": (0.5, 100, 13),
            "efficiency": (0.1, 1, 0.85),
            "reserve_fraction": (0, 0.9, 0.2),
            "supply_w": (1, 100, 15.3),
        },
    )
    full = settings["capacity_wh"] * settings["efficiency"]
    usable = full * (1 - settings["reserve_fraction"])
    return {
        "schema_version": 1,
        "inputs": settings,
        "full_output_wh": full,
        "usable_output_wh": usable,
        "full_runtime_hours": full / settings["load_w"],
        "usable_runtime_hours": usable / settings["load_w"],
        "supply_headroom_w": settings["supply_w"] - settings["load_w"],
        "within_nominal_supply": settings["load_w"] <= settings["supply_w"],
        "note": "Constant-load estimate from declared Wh, efficiency, reserve and load. Supply comparison uses a declared nominal rating, not a measured electrical test. No battery state of charge or measured runtime is inferred.",
    }


def enclosure(values=_UNSET):
    s = checked(
        values,
        {
            "width_mm": (220, 360, 240),
            "height_mm": (145, 260, 160),
            "depth_mm": (55, 100, 70),
            "wall_mm": (2, 5, 3),
            "face_mm": (2, 5, 3),
            "clearance_mm": (0.2, 2, 0.5),
            "screw_inset_mm": (6, 12, 8),
            "hole_diameter_mm": (3, 4.5, 3.4),
        },
    )
    w, h, depth, wall, face, clearance, inset, hole = (s[key] for key in s)
    window = [155.5 + 2 * clearance, 88 + 2 * clearance]
    inner = [w - 2 * wall, h - 2 * wall, depth - wall - face]
    margin = [(inner[0] - 189.5) / 2, (inner[1] - 120) / 2]
    boss = max(inset - wall + 1, hole / 2 + 2)
    frame = [189.5 + 2 * clearance + 16, 120 + 2 * clearance + 16]
    frame_left, frame_top = (w - frame[0]) / 2, (h - frame[1]) / 2
    # Corner posts and the retaining frame must have at least 2 mm separation.
    separation = (
        math.hypot(max(frame_left - inset, 0), max(frame_top - inset, 0)) - boss
    )
    if min(margin) < 6 or inner[2] < 54 or inset - boss < 0.5 or separation < 2:
        raise ValueError(
            "Dimensions need 6 mm display margins, 54 mm inner depth, enclosed corner bosses, and 2 mm frame/post separation."
        )
    corners = [[x, y] for x in (inset, w - inset) for y in (inset, h - inset)]
    retainers = [
        [w / 2 + dx * (189.5 / 2 + clearance + 3), h / 2 + dy * (60 + clearance + 3)]
        for dx in (-1, 1)
        for dy in (-1, 1)
    ]
    return {
        "schema_version": 1,
        "unit": "mm",
        "settings": s,
        "inner_size_mm": inner,
        "display_outline_mm": [189.5, 120, 15],
        "viewing_window_mm": window,
        "display_margin_mm": margin,
        "panel_hole_centres_mm": corners + retainers,
        "corner_boss_radius_mm": boss,
        "retainer_outer_mm": frame,
        "retainer_inner_mm": [183.5, 114],
        "frame_post_separation_mm": separation,
        "assumed_component_stack_mm": 54,
        "validation": "Analytic dimensional checks only. CAD render, print fit, mount retention, cable bends, materials and thermal performance are unverified.",
    }


def _n(value):
    return format(value, ".8g")


def panel_svg(model):
    s = model["settings"]
    w, h = s["width_mm"], s["height_mm"]
    vw, vh = model["viewing_window_mm"]
    holes = "".join(
        f'<circle cx="{_n(x)}" cy="{_n(y)}" r="{_n(s["hole_diameter_mm"] / 2)}"/>'
        for x, y in model["panel_hole_centres_mm"]
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{_n(w)}mm" height="{_n(h)}mm" viewBox="0 0 {_n(w)} {_n(h)}" role="img" aria-labelledby="title desc">
<title id="title">CyberDeck removable front panel, millimetres</title><desc id="desc">Analytic prototype panel. Solid lines show outline, viewing window and eight clearances. Dashed line is the display outline; fit is unverified.</desc>
<g fill="none" stroke="#273d33" stroke-width="0.3"><rect x="0" y="0" width="{_n(w)}" height="{_n(h)}"/><rect x="{_n((w-vw)/2)}" y="{_n((h-vh)/2)}" width="{_n(vw)}" height="{_n(vh)}"/>{holes}<rect x="{_n((w-189.5)/2)}" y="{_n((h-120)/2)}" width="189.5" height="120" stroke-dasharray="2 2"/></g>
<g font-family="monospace" font-size="3" fill="#273d33"><text x="14" y="9">{_n(w)} × {_n(h)} mm · face {_n(s["face_mm"])} mm · holes Ø{_n(s["hole_diameter_mm"])}</text><text x="{_n((w-vw)/2+4)}" y="{_n(h/2)}">VIEW {_n(vw)} × {_n(vh)} mm</text><text x="14" y="{_n(h-7)}">UNBUILT PROTOTYPE · CHECK SCALE AND FIT BEFORE FABRICATION</text></g></svg>\n"""


def enclosure_scad(model):
    s = model["settings"]
    values = ";\n".join(f"{key} = {_n(value)}" for key, value in s.items()) + ";"
    corners = str(model["panel_hole_centres_mm"][:4])
    retainers = str(model["panel_hole_centres_mm"][4:])
    fw, fh = model["retainer_outer_mm"]
    vw, vh = model["viewing_window_mm"]
    return f"""// Generated millimetre prototype; no STL, print-fit or thermal certification.
// Display: official 7-inch Touch Display 2. Pi uses manufacturer's rear mounts.
$fn = 48;
part = "assembly"; // shell, face, retainer, or assembly
{values}
corner_holes = {corners};
retainer_holes = {retainers};
module hole_at(p, height) {{ translate([p[0],p[1],-1]) cylinder(h=height+2,d=hole_diameter_mm); }}
module shell() {{
 difference() {{
  union() {{
   difference() {{ cube([width_mm,height_mm,depth_mm-face_mm]); translate([wall_mm,wall_mm,wall_mm]) cube([width_mm-2*wall_mm,height_mm-2*wall_mm,depth_mm]); }}
   for(p=corner_holes) translate([p[0],p[1],0]) cylinder(h=depth_mm-face_mm,r={_n(model["corner_boss_radius_mm"])});
  }}
  for(p=corner_holes) hole_at(p,depth_mm);
  for(x=[width_mm*.25,width_mm*.45,width_mm*.65]) for(y=[-1,height_mm-wall_mm]) translate([x,y,depth_mm*.55]) cube([24,wall_mm+2,3]);
  translate([width_mm-wall_mm-1,height_mm/2-10,14]) cube([wall_mm+2,20,12]);
 }}
}}
module face() {{ difference() {{ cube([width_mm,height_mm,face_mm]); translate([(width_mm-{_n(vw)})/2,(height_mm-{_n(vh)})/2,-1]) cube([{_n(vw)},{_n(vh)},face_mm+2]); for(p=concat(corner_holes,retainer_holes)) hole_at(p,face_mm); }} }}
module retainer() {{ difference() {{ translate([(width_mm-{_n(fw)})/2,(height_mm-{_n(fh)})/2,0]) cube([{_n(fw)},{_n(fh)},3]); translate([(width_mm-183.5)/2,(height_mm-114)/2,-1]) cube([183.5,114,5]); for(p=retainer_holes) hole_at(p,3); }} }}
assert(width_mm>0 && height_mm>0 && wall_mm>=2);
if(part=="shell") shell();
else if(part=="face") face();
else if(part=="retainer") retainer();
else if(part=="assembly") {{ shell(); translate([0,0,depth_mm-face_mm]) face(); translate([0,0,depth_mm-face_mm-15-3]) retainer(); }}
else assert(false,"Unknown part selector");
"""
