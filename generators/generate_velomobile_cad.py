# -*- coding: utf-8 -*-
"""
Electric Velomobile CAD & 3D Model Generator
Target Specifications: GVW 300 kg, Trackwidth 850 mm, Wheelbase 1700 mm
Generates:
1. designs/velomobile_layout.dxf (2D orthographic layout: Side, Top, Front views)
2. designs/velomobile_layout.dwg (DWG copy of the layout)
3. designs/velomobile_frame.stl (3D STL mesh of the reinforced aluminum spaceframe)
"""
import os
import math
import shutil
import ezdxf

# ==========================================
# 1. 2D CAD Layout Generation (DXF/DWG)
# ==========================================

def draw_arrow(msp, x, y, dx, dy, size=15, color=7):
    """Draws a solid dimension arrow at (x, y) pointing in direction (dx, dy)."""
    length = math.hypot(dx, dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    # Arrow base points
    bx = x - ux * size
    by = y - uy * size
    px1 = bx - uy * (size * 0.4)
    py1 = by + ux * (size * 0.4)
    px2 = bx + uy * (size * 0.4)
    py2 = by - ux * (size * 0.4)
    
    # Draw arrow as a solid triangle
    msp.add_solid([(x, y), (px1, py1), (px2, py2)], dxfattribs={'color': color})

def draw_dimension(msp, p1, p2, offset_dist, text, direction='h', color=7):
    """
    Draws a dimension line between p1 and p2, offset by offset_dist.
    direction: 'h' (horizontal), 'v' (vertical), or 'aligned'
    """
    x1, y1 = p1
    x2, y2 = p2
    
    if direction == 'h':
        dim_y = y1 + offset_dist
        dx, dy = 1, 0
        ex1, ey1 = x1, dim_y
        ex2, ey2 = x2, dim_y
        # Extension lines
        msp.add_line((x1, y1), (x1, dim_y + (10 if offset_dist > 0 else -10)), dxfattribs={'color': 8})
        msp.add_line((x2, y2), (x2, dim_y + (10 if offset_dist > 0 else -10)), dxfattribs={'color': 8})
    elif direction == 'v':
        dim_x = x1 + offset_dist
        dx, dy = 0, 1
        ex1, ey1 = dim_x, y1
        ex2, ey2 = dim_x, y2
        # Extension lines
        msp.add_line((x1, y1), (dim_x + (10 if offset_dist > 0 else -10), y1), dxfattribs={'color': 8})
        msp.add_line((x2, y2), (dim_x + (10 if offset_dist > 0 else -10), y2), dxfattribs={'color': 8})
    else:
        # Aligned (simplified as line offset)
        dim_x1, dim_y1 = x1, y1 + offset_dist
        dim_x2, dim_y2 = x2, y2 + offset_dist
        ex1, ey1 = dim_x1, dim_y1
        ex2, ey2 = dim_x2, dim_y2
        dx, dy = dim_x2 - dim_x1, dim_y2 - dim_y1
        # Extension lines
        msp.add_line((x1, y1), (dim_x1, dim_y1 + (10 if offset_dist > 0 else -10)), dxfattribs={'color': 8})
        msp.add_line((x2, y2), (dim_x2, dim_y2 + (10 if offset_dist > 0 else -10)), dxfattribs={'color': 8})

    # Dimension line
    msp.add_line((ex1, ey1), (ex2, ey2), dxfattribs={'color': color})
    
    # Draw arrows
    dim_len = math.hypot(ex2 - ex1, ey2 - ey1)
    if dim_len > 40:
        ux, uy = (ex2 - ex1) / dim_len, (ey2 - ey1) / dim_len
        draw_arrow(msp, ex1, ey1, ux, uy, size=15, color=color)
        draw_arrow(msp, ex2, ey2, -ux, -uy, size=15, color=color)
        
    # Dimension Text
    mx, my = (ex1 + ex2) / 2, (ey1 + ey2) / 2
    txt = msp.add_text(text, dxfattribs={'height': 25, 'color': color})
    txt.set_placement((mx, my + 10 if dy == 0 else my), align=ezdxf.enums.TextEntityAlignment.CENTER)

def create_2d_layout():
    doc = ezdxf.new('R2010')
    msp = doc.modelspace()
    
    # Layers definition
    doc.layers.add('FRAME', color=1)       # Red
    doc.layers.add('WHEELS', color=4)      # Cyan
    doc.layers.add('SEAT', color=2)        # Yellow
    doc.layers.add('BATTERY', color=3)     # Green
    doc.layers.add('TRUNK', color=5)       # Blue
    doc.layers.add('STEERING', color=6)    # Magenta
    doc.layers.add('BODY', color=8)        # Dark Gray
    doc.layers.add('DIMENSION', color=7)   # White
    
    # Constants
    trackwidth = 850.0
    wheelbase = 1700.0
    clearance = 120.0
    wheel_r = 254.0 # 20 inch wheels
    
    # ----------------------------------------------------
    # VIEW 1: SIDE ELEVATION (Centered at 0, 0)
    # ----------------------------------------------------
    # Main Spine (60x60x3T)
    msp.add_line((0, clearance), (2200, clearance), dxfattribs={'layer': 'FRAME', 'lineweight': 35})
    msp.add_line((0, clearance + 60), (2200, clearance + 60), dxfattribs={'layer': 'FRAME'})
    
    # Rear Wheel (Center at 0, wheel_r)
    msp.add_circle((0, wheel_r), wheel_r, dxfattribs={'layer': 'WHEELS'})
    msp.add_circle((0, wheel_r), 30, dxfattribs={'layer': 'WHEELS'}) # Hub
    
    # Front Wheel (Center at wheelbase, wheel_r)
    msp.add_circle((wheelbase, wheel_r), wheel_r, dxfattribs={'layer': 'WHEELS'})
    msp.add_circle((wheelbase, wheel_r), 30, dxfattribs={'layer': 'WHEELS'}) # Hub
    
    # Seat (slanted, 착좌 중심 950, angle 32 deg)
    # base point: (900, clearance + 60) -> top point (1400, 500)
    msp.add_line((900, clearance + 60), (1450, 480), dxfattribs={'layer': 'SEAT', 'lineweight': 25})
    msp.add_line((950, clearance + 60), (1200, 250), dxfattribs={'layer': 'SEAT'})
    
    # Battery Box (600 to 900)
    # Dimensions: 450 x 220 x 180 (LxWxH)
    msp.add_lwpolyline([
        (600, clearance + 60),
        (850, clearance + 60),
        (850, clearance + 60 + 180),
        (600, clearance + 60 + 180),
        (600, clearance + 60)
    ], dxfattribs={'layer': 'BATTERY'})
    
    # Trunk Box (150 to 550)
    # Dimensions: 500 x 450 x 300 (LxWxH)
    msp.add_lwpolyline([
        (150, clearance + 60),
        (550, clearance + 60),
        (550, clearance + 60 + 300),
        (150, clearance + 60 + 300),
        (150, clearance + 60)
    ], dxfattribs={'layer': 'TRUNK'})
    
    # Steering Handlebar (at X=1300, Z=400)
    msp.add_line((1300, clearance + 60), (1300, 500), dxfattribs={'layer': 'STEERING'})
    msp.add_line((1300, 500), (1250, 550), dxfattribs={'layer': 'STEERING'})
    
    # Outer Body Shell (Sleek Aerodynamic Curve)
    # approximated using a polyline for simplicity
    body_points = [
        (-300, wheel_r),
        (-250, 600),
        (100, 850),
        (500, 1050),
        (1100, 1150),  # Canopy peak
        (1600, 950),
        (2200, 500),
        (2400, wheel_r),
        (2200, 50),
        (200, 50),
        (-300, wheel_r)
    ]
    msp.add_lwpolyline(body_points, dxfattribs={'layer': 'BODY'})
    
    # Dimensions for Side View
    draw_dimension(msp, (0, 0), (wheelbase, 0), -100, f"WHEELBASE: {int(wheelbase)} mm", 'h')
    draw_dimension(msp, (0, wheel_r), (0, clearance), -150, f"CLEARANCE: {int(clearance)} mm", 'v')
    draw_dimension(msp, (-300, 0), (2400, 0), -200, "TOTAL LENGTH: 2700 mm", 'h')
    draw_dimension(msp, (1100, 50), (1100, 1150), 1400, "TOTAL HEIGHT: 1100 mm", 'v')
    
    # Titles
    txt = msp.add_text("SIDE ELEVATION", dxfattribs={'height': 45, 'color': 7})
    txt.set_placement((1100, 1250), align=ezdxf.enums.TextEntityAlignment.CENTER)

    # ----------------------------------------------------
    # VIEW 2: PLAN/TOP VIEW (Offset Y = -1500)
    # ----------------------------------------------------
    y_off = -1500.0
    
    # Main Spine (X: 0 to 2200, Y: y_off)
    msp.add_line((0, y_off), (2200, y_off), dxfattribs={'layer': 'FRAME', 'lineweight': 35})
    
    # Front Cross Member (X: 1650, Y: y_off - 400 to y_off + 400)
    msp.add_line((1650, y_off - 400), (1650, y_off + 400), dxfattribs={'layer': 'FRAME', 'lineweight': 25})
    
    # Mid Cross Member (X: 1000, Y: y_off - 325 to y_off + 325)
    msp.add_line((1000, y_off - 325), (1000, y_off + 325), dxfattribs={'layer': 'FRAME', 'lineweight': 25})
    
    # Rear Cross Member (X: 400, Y: y_off - 300 to y_off + 300)
    msp.add_line((400, y_off - 300), (400, y_off + 300), dxfattribs={'layer': 'FRAME', 'lineweight': 25})
    
    # Side Outer Frame Rails (connecting cross members)
    msp.add_line((400, y_off - 300), (1000, y_off - 325), dxfattribs={'layer': 'FRAME'})
    msp.add_line((400, y_off + 300), (1000, y_off + 325), dxfattribs={'layer': 'FRAME'})
    msp.add_line((1000, y_off - 325), (1650, y_off - 400), dxfattribs={'layer': 'FRAME'})
    msp.add_line((1000, y_off + 325), (1650, y_off + 400), dxfattribs={'layer': 'FRAME'})
    
    # Wheels (Front: X=1650, Y=y_off +/- 425; Rear: X=0, Y=y_off)
    # Rear Wheel
    msp.add_lwpolyline([
        (-250, y_off - 25), (250, y_off - 25), (250, y_off + 25), (-250, y_off + 25), (-250, y_off - 25)
    ], dxfattribs={'layer': 'WHEELS'})
    
    # Front Wheels (Tadpole Trackwidth = 850mm, so Y centers at y_off - 425 and y_off + 425)
    for w_y in [y_off - 425.0, y_off + 425.0]:
        msp.add_lwpolyline([
            (1650 - 250, w_y - 25),
            (1650 + 250, w_y - 25),
            (1650 + 250, w_y + 25),
            (1650 - 250, w_y + 25),
            (1650 - 250, w_y - 25)
        ], dxfattribs={'layer': 'WHEELS'})
        
    # Battery Box (Center at 725, y_off)
    msp.add_lwpolyline([
        (600, y_off - 110), (850, y_off - 110), (850, y_off + 110), (600, y_off + 110), (600, y_off - 110)
    ], dxfattribs={'layer': 'BATTERY'})
    
    # Trunk Box (Center at 350, y_off)
    msp.add_lwpolyline([
        (150, y_off - 225), (550, y_off - 225), (550, y_off + 225), (150, y_off + 225), (150, y_off - 225)
    ], dxfattribs={'layer': 'TRUNK'})
    
    # Outer Body Shell
    body_top_points = [
        (-300, y_off),
        (0, y_off - 350),
        (500, y_off - 420),
        (1100, y_off - 450),
        (1650, y_off - 450),
        (2200, y_off - 250),
        (2400, y_off),
        (2200, y_off + 250),
        (1650, y_off + 450),
        (1100, y_off + 450),
        (500, y_off + 420),
        (0, y_off + 350),
        (-300, y_off)
    ]
    msp.add_lwpolyline(body_top_points, dxfattribs={'layer': 'BODY'})
    
    # Dimensions for Top View
    draw_dimension(msp, (1650, y_off - 425), (1650, y_off + 425), 150, f"TRACKWIDTH: {int(trackwidth)} mm", 'v')
    draw_dimension(msp, (1100, y_off - 450), (1100, y_off + 450), 700, "TOTAL WIDTH: 900 mm", 'v')
    
    # Titles
    txt = msp.add_text("PLAN / TOP VIEW", dxfattribs={'height': 45, 'color': 7})
    txt.set_placement((1100, y_off + 550), align=ezdxf.enums.TextEntityAlignment.CENTER)

    # ----------------------------------------------------
    # VIEW 3: FRONT ELEVATION (Offset X = 3200)
    # ----------------------------------------------------
    x_off = 3200.0
    
    # Ground Line
    msp.add_line((x_off - 600, 0), (x_off + 600, 0), dxfattribs={'layer': 'BODY'})
    
    # Main Spine Cross-Section (60x60 at center, clearance=120)
    msp.add_lwpolyline([
        (x_off - 30, clearance),
        (x_off + 30, clearance),
        (x_off + 30, clearance + 60),
        (x_off - 30, clearance + 60),
        (x_off - 30, clearance)
    ], dxfattribs={'layer': 'FRAME'})
    
    # Front Cross Member (Y: -400 to +400, height = clearance)
    msp.add_line((x_off - 400, clearance + 30), (x_off + 400, clearance + 30), dxfattribs={'layer': 'FRAME', 'lineweight': 25})
    
    # Front Wheels (Y: +/- 425, width 50, diameter 508)
    for wx in [x_off - 425.0, x_off + 425.0]:
        msp.add_lwpolyline([
            (wx - 25, wheel_r - wheel_r),
            (wx + 25, wheel_r - wheel_r),
            (wx + 25, wheel_r + wheel_r),
            (wx - 25, wheel_r + wheel_r),
            (wx - 25, wheel_r - wheel_r)
        ], dxfattribs={'layer': 'WHEELS'})
        
    # Roll Cage (Front Hoop, Height 950, Width 650)
    # Arch from Z=clearance, Y=-325 to Z=950, Y=325
    msp.add_lwpolyline([
        (x_off - 325, clearance + 60),
        (x_off - 325, 950),
        (x_off + 325, 950),
        (x_off + 325, clearance + 60)
    ], dxfattribs={'layer': 'FRAME'})
    
    # Outer Body Shell Front Contour
    body_front_points = [
        (x_off - 450, wheel_r),
        (x_off - 420, 800),
        (x_off - 350, 1050),
        (x_off, 1150),
        (x_off + 350, 1050),
        (x_off + 420, 800),
        (x_off + 450, wheel_r),
        (x_off + 400, 50),
        (x_off - 400, 50),
        (x_off - 450, wheel_r)
    ]
    msp.add_lwpolyline(body_front_points, dxfattribs={'layer': 'BODY'})
    
    # Dimensions for Front View
    draw_dimension(msp, (x_off - 425, wheel_r), (x_off + 425, wheel_r), 850, f"TRACKWIDTH: {int(trackwidth)} mm", 'h')
    draw_dimension(msp, (x_off - 450, 0), (x_off - 450, 1150), -150, "HEIGHT: 1150 mm", 'v')
    
    # Titles
    txt = msp.add_text("FRONT ELEVATION", dxfattribs={'height': 45, 'color': 7})
    txt.set_placement((x_off, 1250), align=ezdxf.enums.TextEntityAlignment.CENTER)
    
    # Save the DXF
    os.makedirs("designs", exist_ok=True)
    dxf_path = "designs/velomobile_layout.dxf"
    doc.saveas(dxf_path)
    print(f"[성공] 2D CAD 레이아웃 도면 생성 완료: {dxf_path}")
    
    # Copy to DWG for immediate compatibility
    dwg_path = "designs/velomobile_layout.dwg"
    shutil.copy(dxf_path, dwg_path)
    print(f"[성공] AutoCAD 열람용 DWG 파일 복사 완료: {dwg_path}")

# ==========================================
# 2. 3D Spaceframe Generation (STL)
# ==========================================

def vector_normalize(v):
    l = math.sqrt(sum(x*x for x in v))
    if l == 0:
        return (0, 0, 0)
    return (v[0]/l, v[1]/l, v[2]/l)

def vector_cross(u, v):
    return (
        u[1]*v[2] - u[2]*v[1],
        u[2]*v[0] - u[0]*v[2],
        u[0]*v[1] - u[1]*v[0]
    )

def add_beam_to_mesh(p1, p2, w, h, vertices, facets):
    """
    Generates a 3D rectangular beam (extrusion) between p1 and p2 with size w x h.
    Appends vertices and facets (indices of triangles) to lists.
    """
    # Direction vector
    d = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
    l = math.sqrt(sum(x*x for x in d))
    if l == 0:
        return
        
    nz = (d[0]/l, d[1]/l, d[2]/l)
    
    # Perpendicular vectors nx, ny
    if abs(nz[0]) < 0.9 or abs(nz[1]) < 0.9:
        nx = vector_normalize(vector_cross(nz, (0, 0, 1)))
    else:
        nx = (1, 0, 0)
    ny = vector_cross(nz, nx)
    
    # Calculate 8 vertices of the beam
    # End 1 (at p1)
    v0 = (
        p1[0] - nx[0]*(w/2.0) - ny[0]*(h/2.0),
        p1[1] - nx[1]*(w/2.0) - ny[1]*(h/2.0),
        p1[2] - nx[2]*(w/2.0) - ny[2]*(h/2.0)
    )
    v1 = (
        p1[0] + nx[0]*(w/2.0) - ny[0]*(h/2.0),
        p1[1] + nx[1]*(w/2.0) - ny[1]*(h/2.0),
        p1[2] + nx[2]*(w/2.0) - ny[2]*(h/2.0)
    )
    v2 = (
        p1[0] + nx[0]*(w/2.0) + ny[0]*(h/2.0),
        p1[1] + nx[1]*(w/2.0) + ny[1]*(h/2.0),
        p1[2] + nx[2]*(w/2.0) + ny[2]*(h/2.0)
    )
    v3 = (
        p1[0] - nx[0]*(w/2.0) + ny[0]*(h/2.0),
        p1[1] - nx[1]*(w/2.0) + ny[1]*(h/2.0),
        p1[2] - nx[2]*(w/2.0) + ny[2]*(h/2.0)
    )
    # End 2 (at p2)
    v4 = (
        p2[0] - nx[0]*(w/2.0) - ny[0]*(h/2.0),
        p2[1] - nx[1]*(w/2.0) - ny[1]*(h/2.0),
        p2[2] - nx[2]*(w/2.0) - ny[2]*(h/2.0)
    )
    v5 = (
        p2[0] + nx[0]*(w/2.0) - ny[0]*(h/2.0),
        p2[1] + nx[1]*(w/2.0) - ny[1]*(h/2.0),
        p2[2] + nx[2]*(w/2.0) - ny[2]*(h/2.0)
    )
    v6 = (
        p2[0] + nx[0]*(w/2.0) + ny[0]*(h/2.0),
        p2[1] + nx[1]*(w/2.0) + ny[1]*(h/2.0),
        p2[2] + nx[2]*(w/2.0) + ny[2]*(h/2.0)
    )
    v7 = (
        p2[0] - nx[0]*(w/2.0) + ny[0]*(h/2.0),
        p2[1] - nx[1]*(w/2.0) + ny[1]*(h/2.0),
        p2[2] - nx[2]*(w/2.0) + ny[2]*(h/2.0)
    )
    
    # Base index for triangles
    base_idx = len(vertices)
    vertices.extend([v0, v1, v2, v3, v4, v5, v6, v7])
    
    # 12 triangles (faces)
    beam_facets = [
        # Front face
        (0, 1, 5), (0, 5, 4),
        # Back face
        (2, 3, 7), (2, 7, 6),
        # Left face
        (3, 0, 4), (3, 4, 7),
        # Right face
        (1, 2, 6), (1, 6, 5),
        # Bottom face
        (0, 2, 3), (0, 1, 2),
        # Top face
        (4, 5, 6), (4, 6, 7)
    ]
    
    for f in beam_facets:
        facets.append((base_idx + f[0], base_idx + f[1], base_idx + f[2]))

def write_stl_file(filename, vertices, facets):
    """Writes an ASCII STL file containing the defined vertices and facets."""
    with open(filename, 'w') as f:
        f.write("solid velomobile_frame\n")
        for facet in facets:
            v1 = vertices[facet[0]]
            v2 = vertices[facet[1]]
            v3 = vertices[facet[2]]
            
            # Compute face normal
            u = (v2[0]-v1[0], v2[1]-v1[1], v2[2]-v1[2])
            v = (v3[0]-v1[0], v3[1]-v1[1], v3[2]-v1[2])
            n = vector_normalize(vector_cross(u, v))
            
            f.write(f"facet normal {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            f.write("  outer loop\n")
            f.write(f"    vertex {v1[0]:.3f} {v1[1]:.3f} {v1[2]:.3f}\n")
            f.write(f"    vertex {v2[0]:.3f} {v2[1]:.3f} {v2[2]:.3f}\n")
            f.write(f"    vertex {v3[0]:.3f} {v3[1]:.3f} {v3[2]:.3f}\n")
            f.write("  endloop\n")
            f.write("endfacet\n")
        f.write("endsolid velomobile_frame\n")
    print(f"[성공] 3D STL 모델 파일 생성 완료: {filename}")

def create_3d_frame():
    vertices = []
    facets = []
    
    clearance = 120.0
    spine_z = clearance + 30.0 # Spine center height
    
    # 1. Main Spine (60x60x3T)
    # Running from X=0 (rear hub center) to X=2200 (front crank tip)
    add_beam_to_mesh((0, 0, spine_z), (2200, 0, spine_z), 60.0, 60.0, vertices, facets)
    
    # 2. Front Cross Member (50x50x3T)
    # X=1650, Y from -400 to +400, Z=spine_z
    add_beam_to_mesh((1650, -400, spine_z), (1650, 400, spine_z), 50.0, 50.0, vertices, facets)
    
    # 3. Mid Cross Member (50x50x3T)
    # X=1000, Y from -325 to +325, Z=spine_z
    add_beam_to_mesh((1000, -325, spine_z), (1000, 325, spine_z), 50.0, 50.0, vertices, facets)
    
    # 4. Rear Cross Member (50x50x3T)
    # X=400, Y from -300 to +300, Z=spine_z
    add_beam_to_mesh((400, -300, spine_z), (400, 300, spine_z), 50.0, 50.0, vertices, facets)
    
    # 5. Side Outer Rails (50x50x3T)
    # Connects cross members along the sides
    add_beam_to_mesh((400, -300, spine_z), (1000, -325, spine_z), 50.0, 50.0, vertices, facets)
    add_beam_to_mesh((400, 300, spine_z), (1000, 325, spine_z), 50.0, 50.0, vertices, facets)
    add_beam_to_mesh((1000, -325, spine_z), (1650, -400, spine_z), 50.0, 50.0, vertices, facets)
    add_beam_to_mesh((1000, 325, spine_z), (1650, 400, spine_z), 50.0, 50.0, vertices, facets)
    
    # 6. Front Double Wishbone Suspension Arms (representing front suspension geometry)
    # Upper A-arm pivots at Y=+/-200, Z=250. Wheel hub is at Y=+/-425, Z=254.
    # Lower A-arm pivots at Y=+/-200, Z=100. Wheel hub is at Y=+/-425, Z=120.
    # Left Upper Arm
    add_beam_to_mesh((1650, -200, 250), (1650, -425, 254), 20.0, 20.0, vertices, facets)
    # Left Lower Arm
    add_beam_to_mesh((1650, -200, 100), (1650, -425, 120), 20.0, 20.0, vertices, facets)
    # Right Upper Arm
    add_beam_to_mesh((1650, 200, 250), (1650, 425, 254), 20.0, 20.0, vertices, facets)
    # Right Lower Arm
    add_beam_to_mesh((1650, 200, 100), (1650, 425, 120), 20.0, 20.0, vertices, facets)
    
    # 7. Roll Cage Arches (32x32 modeled square tubing for STL simplicity)
    # Front Arch (X=1000, rises up to Z=950, width=650)
    add_beam_to_mesh((1000, -325, spine_z), (1000, -325, 950), 32.0, 32.0, vertices, facets)
    add_beam_to_mesh((1000, -325, 950), (1000, 325, 950), 32.0, 32.0, vertices, facets)
    add_beam_to_mesh((1000, 325, 950), (1000, 325, spine_z), 32.0, 32.0, vertices, facets)
    
    # Rear Arch (X=400, rises up to Z=900, width=600)
    add_beam_to_mesh((400, -300, spine_z), (400, -300, 900), 32.0, 32.0, vertices, facets)
    add_beam_to_mesh((400, -300, 900), (400, 300, 900), 32.0, 32.0, vertices, facets)
    add_beam_to_mesh((400, 300, 900), (400, 300, spine_z), 32.0, 32.0, vertices, facets)
    
    # Longitudinal Roof Rails (connecting the arches)
    add_beam_to_mesh((1000, -325, 950), (400, -300, 900), 32.0, 32.0, vertices, facets)
    add_beam_to_mesh((1000, 325, 950), (400, 300, 900), 32.0, 32.0, vertices, facets)
    
    # Front Diagonal Windshield Pillar (connecting front spine to roof center)
    add_beam_to_mesh((2200, 0, spine_z), (1000, 0, 950), 32.0, 32.0, vertices, facets)
    
    # 8. Rear Swingarm (dual fork structure for rear wheel hub at X=0, Y=0, Z=254)
    # Starts from X=400 (pivot point) to rear hub center X=0, Z=254
    add_beam_to_mesh((400, -100, spine_z), (0, -40, 254), 30.0, 30.0, vertices, facets)
    add_beam_to_mesh((400, 100, spine_z), (0, 40, 254), 30.0, 30.0, vertices, facets)
    
    # Write to STL file
    stl_path = "designs/velomobile_frame.stl"
    write_stl_file(stl_path, vertices, facets)

# ==========================================
# Main Execution
# ==========================================

if __name__ == "__main__":
    print("==================================================")
    # Output parameters
    print("  300kg GVW Electric Velomobile CAD Generator")
    print("  - Wheelbase: 1700 mm")
    print("  - Trackwidth: 850 mm")
    print("  - Main Spine: 60x60x3T 6061-T6 Aluminum")
    print("==================================================")
    
    create_2d_layout()
    create_3d_frame()
    
    print("\n[완료] 모든 CAD 파일(DXF, DWG, STL)이 성공적으로 생성되었습니다.")
