# Assembly and physical evidence plan

This is an unbuilt prototype. No hardware was purchased, wired, printed, or tested. The [BOM](BOM.csv) is a proposed parts list, not a verified kit or compatibility guarantee. Do not order a full set until the measurements below agree.

The selected display is the **7-inch** official Touch Display 2, rotated to landscape. The [manufacturer guide](https://www.raspberrypi.com/documentation/accessories/touch-display-2.html) gives a 189.5 × 120 × 15 mm outline and a 155.5 × 88 mm viewing area in this orientation. It also gives the appropriate Pi 4 DSI/power connections and rear mounting procedure. Follow that guide; keep power disconnected during assembly. Do not drill glass or copy a connector orientation from the concept cover.

The Pi 4 reference board is 85 × 56 mm, with a 58 × 49 mm mounting pattern, from the [official mechanical drawing](https://datasheets.raspberrypi.com/rpi4/raspberry-pi-4-mechanical-drawing.pdf). The enclosure does not fabricate matching board standoffs: the Pi uses the manufacturer's display mounts. Display mount geometry and the assembled board position must be checked on the actual components.

1. Measure the received display, board, supplied mounts, plugs, cable bends and cooling parts. Record the part revisions, instruments, dimensions and photos. Check that neither clamp rails nor fasteners contact rear components or the active glass area.
2. Print the SVG at actual size and verify its 240 × 160 mm outline with a ruler. Test a cardboard or dummy-panel fit first. The SVG is an annotated drawing, not machine-ready toolpaths. Its dashed line shows the display outline; text and guide lines are not cut instructions.
3. Inspect the OpenSCAD source. Select `shell`, `face`, or `retainer` for separate export. Render in OpenSCAD and inspect for intersections and adequate material before generating any mesh. This task has not run a CAD engine or checked a printable mesh.
4. Choose material, print settings and hardware only after reviewing actual temperature and load requirements. Check hole sizes, edge distances, clamp pressure, retained nuts and access to all fasteners. Default fastener lengths apply only to the default enclosure and remain unverified.
5. Connect only the manufacturer's supplied/display-approved connections. Start with the correct mains adapter on the bench. No custom battery-cell, charging or mains circuit is supplied. Keep a proposed portable source external until its voltage, current, protection and cable behaviour are checked under load.
6. Boot the target OS outside the enclosure. Compare dashboard live values with the OS. Check display rotation and touch orientation with the target desktop tools before optional kiosk startup.
7. Fit components without forced cables or contact against conductive parts. Test retention and strain relief, then measure current, voltage drop, temperatures and behaviour at idle and sustained workload. Stop if components exceed their manufacturer limits. Slots do not establish cooling performance.
8. Measure actual portable runtime separately. Record pack specification, usable energy, workload, ambient conditions and shutdown criterion. Compare it with the model only when the inputs match. The model is not remaining charge telemetry.

The source reserves 54 mm of internal depth as an **unverified allowance**: display 15 mm, mount 8 mm, board 18 mm, cable 10 mm, retainer 3 mm. Default internal depth is 64 mm. This bookkeeping is not a fit calculation from a complete component assembly. The model also checks 6 mm display margins and 2 mm frame/post separation; tolerances and deformation remain physical checks.

Keep assembly, boot, CAD, retention, electrical, runtime and thermal results marked **pending** until direct evidence exists. A generated cover and simulated dashboard cannot close these checks.
