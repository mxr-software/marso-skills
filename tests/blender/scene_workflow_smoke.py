"""Run in Blender with --python-exit-code 1; no cloud or external assets."""
import bpy
import json
import math
from pathlib import Path
import runpy
import tempfile

ROOT=Path(__file__).resolve().parents[2]
shell=runpy.run_path(str(ROOT/'skills/blender/marso-blender-blockout/scripts/room_shell.py'))['build']
rig=runpy.run_path(str(ROOT/'skills/blender/marso-blender-camera/scripts/camera_rig.py'))
place=runpy.run_path(str(ROOT/'skills/blender/marso-blender-place-scene/scripts/place_in_blender.py'))['place']
bpy.ops.wm.read_factory_settings(use_empty=True)
result=shell({'run_id':'room-test','size':[4,6,2.7],'openings':[{'wall':0,'start':1,'width':.9,'bottom':0,'height':2.1}]})
before=len(bpy.data.objects)
for spec in [{'run_id':'room-test','size':[4,6,2.7]}, {'run_id':'bad','size':[4,6,2.7],'corners':[[0,0],[4,0],[3,5],[0,6]]},
             {'run_id':'bad-opening','size':[4,6,2.7],'openings':[{'wall':0,'start':3.8,'width':.9,'bottom':0,'height':2.1}]}]:
    try:shell(spec)
    except ValueError:pass
    else:raise AssertionError('Invalid shell accepted')
    assert len(bpy.data.objects)==before
angled=shell({'run_id':'angled','size':[4,6,2.7],'origin':[10,0,0],'corners':[[0,0],[4,0],[3,5],[0,6]],'nonorthogonal_reason':'Provided design plan'})
star=[[math.cos(i*2*math.pi/5),math.sin(i*2*math.pi/5)] for i in (0,2,4,1,3)]
before=len(bpy.data.objects)
try:shell({'run_id':'star','size':[4,6,2.7],'corners':star,'nonorthogonal_reason':'Invalid self-crossing input'})
except ValueError:pass
else:raise AssertionError('Self-crossing shell accepted')
assert len(bpy.data.objects)==before
floor=bpy.data.objects[result['anchors'][0]['entity']];old=floor.matrix_world.copy()
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp)/'placement.json'
    doc={'run_id':'placed','anchors':[{'global_id':'floor','name':'Floor','kind':'support','existing_entity':floor.name}],
         'objects':[{'global_id':'bench','name':'Bench','asset_id':'a1','parent':'floor','relation':'on','kind':'model','route':'model','order':0,
                     'dimensions_m':[2,.7,.9],'location':[2,3,0],'flags':[]}]}
    p.write_text(json.dumps(doc));place(str(p));place(str(p))
    assert floor.matrix_world==old
    assert len([o for o in bpy.data.objects if o.get('marso_global_id')=='bench' and o.get('marso_role')=='entity'])==1
scene=bpy.context.scene
unchanged=(scene.camera,scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base,scene.render.resolution_x,scene.render.use_motion_blur)
camera=rig['build']({'id':'smooth','keys':[{'frame':1,'position':[2,1,1.5],'aim':[2,5,1.2]}, {'frame':25,'position':[2,2,1.5],'aim':[2,5,1.2]}]})
assert unchanged==(scene.camera,scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base,scene.render.resolution_x,scene.render.use_motion_blur)
ob=bpy.data.objects[camera['camera']]
report=rig['clearance_report'](ob,[o for o in bpy.data.collections[result['collection']].objects if o.type=='MESH'])
assert report['passed'],report
cross=rig['build']({'id':'cross','keys':[{'frame':1,'position':[2,5.5,1],'aim':[2,9,1]}, {'frame':25,'position':[2,7,1],'aim':[2,9,1]}]})
assert not rig['clearance_report'](bpy.data.objects[cross['camera']],[o for o in bpy.data.collections[result['collection']].objects if o.type=='MESH'])['passed']
count=len(bpy.data.objects)
try:rig['build']({'id':'bad-focus','keys':[{'frame':1,'position':[0,0,0],'aim':[0,0,0]}]})
except ValueError:pass
else:raise AssertionError('Zero focus accepted')
assert len(bpy.data.objects)==count
held=rig['build']({'id':'eased-hold','fps':24,'resolution':[160,96],'easing':'smoothstep','handheld':'none','keys':[
    {'frame':1,'position':[2,1,1.5],'aim':[2,5,1.2]},
    {'frame':49,'position':[2,1,1.5],'aim':[2,5,1.2]},
    {'frame':97,'position':[2,3,1.5],'aim':[2,5,1.2]}]})
held_ob=bpy.data.objects[held['camera']];scene=bpy.context.scene;positions=[]
for frame in range(1,98):
    scene.frame_set(frame);positions.append(held_ob.location.copy())
assert all((p-positions[0]).length<1e-7 for p in positions[:49]),'Base hold moved'
steps=[(b-a).length for a,b in zip(positions[48:],positions[49:])]
assert steps[0]<max(steps)/10 and steps[-1]<max(steps)/10,'Endpoints did not ease'
linear=bpy.data.objects[camera['camera']]
scene.frame_set(1);a=linear.location.copy();scene.frame_set(13);b=linear.location.copy();scene.frame_set(25);c=linear.location.copy()
assert ((b-a)-(c-b)).length<1e-6,'Default interpolation changed'
for spec in [dict(id='bad-easing',easing='unknown',keys=[{'frame':1,'position':[0,0,0],'aim':[1,1,1]}])]:
    count=len(bpy.data.objects)
    try:rig['build'](spec)
    except ValueError:pass
    else:raise AssertionError('Invalid easing accepted')
    assert len(bpy.data.objects)==count
scene.render.engine='BLENDER_WORKBENCH'
old=(scene.camera,scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base,scene.render.resolution_x)
try:rig['apply_output_settings'](held,motion_blur=True)
except ValueError:pass
else:raise AssertionError('Workbench blur accepted')
assert old==(scene.camera,scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base,scene.render.resolution_x)
for bad in [dict(held,resolution=[1,96]),dict(held,frames=[-1,97])]:
    try:rig['apply_output_settings'](bad,motion_blur=False)
    except ValueError:pass
    else:raise AssertionError('Out-of-range output accepted')
    assert old==(scene.camera,scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base,scene.render.resolution_x)
applied=rig['apply_output_settings'](dict(held,fps=24000/1001),motion_blur=False)
assert scene.camera==held_ob and [scene.frame_start,scene.frame_end]==[1,97]
assert abs(applied['effective_fps']-24000/1001)<1e-4
assert applied['resolution']==[160,96] and scene.render.resolution_percentage==100 and not scene.render.use_motion_blur
scene.render.engine='CYCLES'
applied=rig['apply_output_settings'](held,motion_blur=True)
assert applied['motion_blur'] and abs(scene.render.motion_blur_shutter-.5)<1e-6
rig['apply_output_settings'](held,motion_blur=False)
assert not scene.render.use_motion_blur
print('PASS: camera linear default, eased endpoints, base hold, fractional fps, output settings and explicit blur toggle')
print('PASS: shell validation, non-square exception, accepted-shell placement/resume, camera clearance and rollback')
