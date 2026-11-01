"""Build a versioned blockout shell in Blender; no automatic reconstruction."""
import math
import bpy
from mathutils import Vector


def build(spec):
    run = spec['run_id']
    if not isinstance(run, str) or not run.strip():
        raise ValueError('run_id must be nonempty')
    if any(c.get('marso_shell_run') == run for c in bpy.data.collections):
        raise ValueError('Shell run exists; preserve it or choose a new revision')
    w, d, h = map(float, spec['size'])
    thick = float(spec.get('thickness', .15))
    if not all(math.isfinite(x) and x > 0 for x in (w, d, h, thick)):
        raise ValueError('Positive finite size and thickness required')
    corners = [Vector(p) for p in spec.get('corners', [(0, 0), (w, 0), (w, d), (0, d)])]
    if len(corners) < 3 or any(len(p) != 2 or not all(math.isfinite(x) for x in p) for p in corners):
        raise ValueError('Finite 2D footprint required')
    edges = [corners[(i+1) % len(corners)]-p for i, p in enumerate(corners)]
    if any(e.length < 1e-5 for e in edges):
        raise ValueError('Repeated footprint corner')
    crosses = [e.x*edges[(i+1) % len(edges)].y-e.y*edges[(i+1) % len(edges)].x for i, e in enumerate(edges)]
    if any(c <= 1e-8 for c in crosses):
        raise ValueError('Footprint must be strictly convex and counterclockwise')
    if any(e.x*(q-p).y-e.y*(q-p).x < -1e-8 for p,e in zip(corners,edges) for q in corners):
        raise ValueError('Self-crossing/nonconvex footprint is unsupported')
    if any(abs(e.normalized().dot(edges[(i+1) % len(edges)].normalized())) > 1e-5 for i, e in enumerate(edges)):
        if not str(spec.get('nonorthogonal_reason', '')).strip():
            raise ValueError('Non-right corner requires nonorthogonal_reason')
    origin = tuple(map(float, spec.get('origin', (0, 0, 0))))
    yaw = float(spec.get('yaw_deg', 0))
    if len(origin) != 3 or not all(math.isfinite(x) for x in (*origin, yaw)):
        raise ValueError('Invalid root transform')
    openings = {i: [] for i in range(len(edges))}
    for op in spec.get('openings', []):
        i = op['wall']
        if type(i) is not int or i not in openings:
            raise ValueError('Unknown opening wall')
        a, width, bottom, height = (float(op[k]) for k in ('start', 'width', 'bottom', 'height'))
        b, top = a+width, bottom+height
        if not all(math.isfinite(x) for x in (a, width, bottom, height)) or not (0 <= a < b <= edges[i].length and 0 <= bottom < top <= h):
            raise ValueError('Opening lies outside wall or has invalid dimensions')
        if any(not (b < x[0] or a > x[1] or top < x[2] or bottom > x[3]) for x in openings[i]):
            raise ValueError('Touching/overlapping openings need an explicit combined design')
        openings[i].append((a, b, bottom, top))
    coll = bpy.data.collections.new('Shell '+run);coll['marso_shell_run'] = run
    bpy.context.scene.collection.children.link(coll)
    root = bpy.data.objects.new('Shell '+run, None);coll.objects.link(root)
    root.location = origin;root.rotation_euler.z = math.radians(yaw)
    anchors = []

    def entity(key):
        obj = bpy.data.objects.new(key, None);coll.objects.link(obj);obj.parent = root
        group = bpy.data.objects.new(key+'__geometry', None);coll.objects.link(group);group.parent = obj
        obj['marso_shell_id'] = key
        anchors.append({'id': key, 'entity': obj.name, 'geometry': group.name})
        return group

    def box(group, name, centre, size, angle=0):
        sx, sy, sz = size
        verts = [(x*sx/2, y*sy/2, z*sz/2) for z in (-1, 1) for y in (-1, 1) for x in (-1, 1)]
        mesh = bpy.data.meshes.new(name);mesh.from_pydata(verts, [], [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]);mesh.update()
        obj = bpy.data.objects.new(name, mesh);coll.objects.link(obj);obj.parent = group
        obj.location = centre;obj.rotation_euler.z = angle
    floor = entity('floor')
    verts = [(p.x,p.y,z) for z in (-thick,0) for p in corners];n=len(corners)
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh = bpy.data.meshes.new('floor');mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('floor__surface',mesh);coll.objects.link(obj);obj.parent=floor
    for i, (p, edge) in enumerate(zip(corners, edges)):
        group=entity('wall-'+str(i));direction=edge.normalized();outward=Vector((direction.y,-direction.x))
        xs=sorted({0,edge.length,*[v for o in openings[i] for v in o[:2]]})
        zs=sorted({0,h,*[v for o in openings[i] for v in o[2:]]})
        for a,b in zip(xs,xs[1:]):
            for low,high in zip(zs,zs[1:]):
                x,z=(a+b)/2,(low+high)/2
                if any(oa <= x <= ob and ol <= z <= oh for oa,ob,ol,oh in openings[i]):continue
                left=a-thick if a==0 else a
                right=b+thick if b==edge.length else b
                c=p+direction*((left+right)/2)+outward*thick/2
                box(group,f'wall-{i}__panel',(c.x,c.y,z),(right-left,thick,high-low),math.atan2(edge.y,edge.x))
    bpy.context.view_layer.update()
    for i,row in enumerate(anchors[1:]):
        a,b=(root.matrix_world@Vector((p.x,p.y,0)) for p in (corners[i],corners[(i+1)%n]))
        row['floor_line']=[list(a[:2]),list(b[:2])];row['wall_height']=h;row['floor_z']=origin[2]
    return {'run_id':run,'root':root.name,'collection':coll.name,'anchors':anchors}
