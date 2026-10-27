// Generated millimetre prototype; no STL, print-fit or thermal certification.
// Display: official 7-inch Touch Display 2. Pi uses manufacturer's rear mounts.
$fn = 48;
part = "assembly"; // shell, face, retainer, or assembly
width_mm = 240;
height_mm = 160;
depth_mm = 70;
wall_mm = 3;
face_mm = 3;
clearance_mm = 0.5;
screw_inset_mm = 8;
hole_diameter_mm = 3.4;
corner_holes = [[8, 8], [8, 152], [232, 8], [232, 152]];
retainer_holes = [[21.75, 16.5], [21.75, 143.5], [218.25, 16.5], [218.25, 143.5]];
module hole_at(p, height) { translate([p[0],p[1],-1]) cylinder(h=height+2,d=hole_diameter_mm); }
module shell() {
 difference() {
  union() {
   difference() { cube([width_mm,height_mm,depth_mm-face_mm]); translate([wall_mm,wall_mm,wall_mm]) cube([width_mm-2*wall_mm,height_mm-2*wall_mm,depth_mm]); }
   for(p=corner_holes) translate([p[0],p[1],0]) cylinder(h=depth_mm-face_mm,r=6);
  }
  for(p=corner_holes) hole_at(p,depth_mm);
  for(x=[width_mm*.25,width_mm*.45,width_mm*.65]) for(y=[-1,height_mm-wall_mm]) translate([x,y,depth_mm*.55]) cube([24,wall_mm+2,3]);
  translate([width_mm-wall_mm-1,height_mm/2-10,14]) cube([wall_mm+2,20,12]);
 }
}
module face() { difference() { cube([width_mm,height_mm,face_mm]); translate([(width_mm-156.5)/2,(height_mm-89)/2,-1]) cube([156.5,89,face_mm+2]); for(p=concat(corner_holes,retainer_holes)) hole_at(p,face_mm); } }
module retainer() { difference() { translate([(width_mm-206.5)/2,(height_mm-137)/2,0]) cube([206.5,137,3]); translate([(width_mm-183.5)/2,(height_mm-114)/2,-1]) cube([183.5,114,5]); for(p=retainer_holes) hole_at(p,3); } }
assert(width_mm>0 && height_mm>0 && wall_mm>=2);
if(part=="shell") shell();
else if(part=="face") face();
else if(part=="retainer") retainer();
else if(part=="assembly") { shell(); translate([0,0,depth_mm-face_mm]) face(); translate([0,0,depth_mm-face_mm-15-3]) retainer(); }
else assert(false,"Unknown part selector");
