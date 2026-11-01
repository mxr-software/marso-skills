"""Explicit-key camera rig for Blender; preserves existing rigs and scene settings."""
import hashlib
import json
import math
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def vec(value):
    if len(value) != 3 or not all(isinstance(x, (int,float)) and math.isfinite(x) for x in value):
        raise ValueError('Expected a finite world-space 3-vector')
    return Vector(value)


def build(spec):
    name=spec['id'];keys=spec['keys'];fps=float(spec.get('fps',24));lens=float(spec.get('lens_mm',50))
    fstop=float(spec.get('fstop',5.6));shutter=float(spec.get('shutter_frames',.5));amount=float(spec.get('amount',1))
    mode=spec.get('handheld','none');resolution=spec.get('resolution',[1920,1080]);easing=spec.get('easing','linear')
    if not isinstance(name,str) or not name.strip() or not keys:raise ValueError('id and keys required')
    if any(o.get('marso_shot_id') == name for o in bpy.data.objects):raise ValueError('Shot exists; use a new revision')
    if mode not in ('none','standing','walking'):raise ValueError('Unknown handheld mode')
    if easing not in ('linear','smoothstep'):raise ValueError('Unknown segment easing')
    if not all(math.isfinite(x) and x > 0 for x in (fps,lens,fstop)) or not 0 <= shutter <= 2 or not 0 <= amount <= 3:raise ValueError('Invalid camera settings')
    if len(resolution)!=2 or any(type(x) is not int or x<=0 for x in resolution):raise ValueError('Invalid resolution')
    frames=[k['frame'] for k in keys]
    if any(type(f) is not int for f in frames) or any(a>=b for a,b in zip(frames,frames[1:])):raise ValueError('Strictly increasing integer frames required')
    points=[(vec(k['position']),vec(k['aim']),vec(k.get('focus',k['aim']))) for k in keys]
    samples=[];index=0;previous=None;speed=0
    for frame in range(frames[0],frames[-1]+1):
        while index+1<len(frames)-1 and frame>frames[index+1]:index+=1
        end=min(index+1,len(keys)-1);t=0 if end==index else (frame-frames[index])/(frames[end]-frames[index])
        if easing=='smoothstep':t=t*t*(3-2*t)
        pos,aim,focus=[a.lerp(b,t) for a,b in zip(points[index],points[end])]
        instant=(pos-previous).length*fps if previous is not None else 0
        speed+=(instant-speed)*(1-math.exp(-1/(fps*.15)));previous=pos.copy()
        if (aim-pos).length<.01 or (focus-pos).length<.01:raise ValueError('Camera crosses aim/focus target')
        seconds=(frame-frames[0])/fps
        if mode!='none':
            rotation=(aim-pos).to_track_quat('-Z','Y')
            walk=min(speed/.6,1) if mode=='walking' else 0
            offset=Vector((.003*math.sin(seconds*2.1), .002*math.sin(seconds*3.2)+.008*walk*math.sin(seconds*11),0))*amount
            pos+=rotation@offset
        samples.append((frame,pos,aim,focus,speed))
    # Validate all samples before creating scene data.
    data=bpy.data.cameras.new(name);camera=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(camera)
    data.lens=lens;data.dof.use_dof=True;data.dof.aperture_fstop=fstop
    camera.rotation_mode='QUATERNION';camera['marso_shot_id']=name
    last_rotation=None
    for frame,pos,aim,focus,speed in samples:
        camera.location=pos;rotation=(aim-pos).to_track_quat('-Z','Y')
        if last_rotation is not None and rotation.dot(last_rotation)<0:rotation.negate()
        camera.rotation_quaternion=rotation;last_rotation=rotation.copy()
        data.dof.focus_distance=(focus-pos).length
        camera.keyframe_insert('location',frame=frame);camera.keyframe_insert('rotation_quaternion',frame=frame)
        data.keyframe_insert('dof.focus_distance',frame=frame)
    # Blender 5.x actions are slotted; keep subframe interpolation predictable.
    for owner in (camera,data):
        action=owner.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
    revision=hashlib.sha256(json.dumps(spec,sort_keys=True,allow_nan=False).encode()).hexdigest()
    camera['marso_shot_revision']=revision
    return {'camera':camera.name,'revision':revision,'frames':[frames[0],frames[-1]],'fps':fps,'resolution':resolution,'shutter_frames':shutter,
            'easing':easing,'limits':'Explicit path with linear baked subframes; inspect preview. Scene output and blur settings are unchanged.'}


def apply_output_settings(shot, *, motion_blur=False):
    """Explicitly apply a build result to the current scene; blur is verified for Cycles only."""
    scene=bpy.context.scene;render=scene.render
    camera=scene.objects.get(shot['camera'])
    if camera is None or camera.type!='CAMERA':raise ValueError('Shot camera must belong to the current scene')
    if type(motion_blur) is not bool:raise ValueError('motion_blur must be a boolean')
    if motion_blur and render.engine!='CYCLES':raise ValueError('Motion blur output is supported only for Cycles; choose Cycles explicitly')
    fps=float(shot['fps']);shutter=float(shot['shutter_frames'])
    if not math.isfinite(fps) or fps<=0 or not math.isfinite(shutter) or not 0<=shutter<=2:raise ValueError('Invalid fps or shutter')
    frames=shot['frames'];resolution=shot['resolution']
    if len(frames)!=2 or any(type(f) is not int for f in frames) or frames[0]>frames[1]:raise ValueError('Invalid frame range')
    if len(resolution)!=2 or any(type(v) is not int for v in resolution):raise ValueError('Invalid resolution')
    nominal_fps=max(1,round(fps));base=nominal_fps/fps
    settings=[(scene,'frame_start',frames[0]),(scene,'frame_end',frames[1]),
              (render,'fps',nominal_fps),(render,'fps_base',base),
              (render,'resolution_x',resolution[0]),(render,'resolution_y',resolution[1]),
              (render,'resolution_percentage',100),(render,'motion_blur_shutter',shutter)]
    # Check RNA bounds before mutation: Blender otherwise silently clamps values.
    for owner,name,value in settings:
        prop=owner.bl_rna.properties.get(name)
        if prop is None or not prop.hard_min<=value<=prop.hard_max:raise ValueError('Unsupported output setting: '+name)
    if not hasattr(render,'use_motion_blur'):raise ValueError('Renderer motion-blur API is unavailable')
    for owner,name,value in settings:setattr(owner,name,value)
    render.use_motion_blur=motion_blur;scene.camera=camera
    return {'camera':camera.name,'frames':[scene.frame_start,scene.frame_end],
            'fps':render.fps,'fps_base':render.fps_base,'effective_fps':render.fps/render.fps_base,
            'resolution':[render.resolution_x,render.resolution_y],'resolution_percentage':render.resolution_percentage,
            'engine':render.engine,'motion_blur':render.use_motion_blur,'shutter_frames':render.motion_blur_shutter}


def clearance_report(camera, objects, clearance=.15):
    if not math.isfinite(clearance) or clearance<0:raise ValueError('Invalid clearance')
    scene=bpy.context.scene;start=scene.frame_current;trees=[];dg=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type!='MESH':continue
        evaluated=obj.evaluated_get(dg);mesh=evaluated.to_mesh()
        try:trees.append((obj.name,BVHTree.FromPolygons([obj.matrix_world@v.co for v in mesh.vertices],[list(p.vertices) for p in mesh.polygons])))
        finally:evaluated.to_mesh_clear()
    action=camera.animation_data.action;lo,hi=map(int,action.frame_range);issues=[];previous=None
    try:
        for frame in range(lo,hi+1):
            scene.frame_set(frame);pos=camera.matrix_world.translation.copy()
            for name,tree in trees:
                nearest=tree.find_nearest(pos)
                if nearest[0] is not None and nearest[3]<clearance:issues.append({'frame':frame,'object':name,'kind':'near','distance':nearest[3]})
                if previous is not None and (pos-previous).length>1e-8:
                    delta=pos-previous;hit=tree.ray_cast(previous,delta.normalized(),delta.length)
                    if hit[0] is not None:issues.append({'frame':frame,'object':name,'kind':'crossing'})
            previous=pos
    finally:scene.frame_set(start)
    return {'issues':issues,'passed':not issues,'scope':'Static obstacle surfaces, sampled camera centre and adjacent path segments; not frustum clearance'}
