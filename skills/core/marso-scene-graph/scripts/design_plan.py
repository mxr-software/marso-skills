"""Convert an explicit design (not detections) into asset and placement plans."""
import argparse
import json
import math
from pathlib import Path


def vector(value, positive=False):
    if not isinstance(value,list) or len(value)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) or (positive and v<=0) for v in value):
        raise ValueError('Expected finite three-component vector'+(' with positive dimensions' if positive else ''))
    return value


def build(doc):
    if doc.get('schema')!='marso/scene-design@1' or not isinstance(doc.get('run_id'),str) or not doc['run_id'].strip():raise ValueError('scene-design@1 and run_id required')
    assets=[];objects=[];ids=set();aids=set();anchors=doc.get('anchors',[])
    if not isinstance(anchors,list):raise ValueError('anchors must be a list')
    for row in anchors:
        gid=row.get('global_id')
        if not isinstance(gid,str) or not gid or gid in ids or not row.get('existing_entity'):raise ValueError('Unique anchor id and existing_entity required')
        ids.add(gid)
    for source in doc.get('assets',[]):
        aid=source['id'];route=source['route'];label=source['label'];instances=source['instances']
        if not isinstance(aid,str) or not aid or aid in aids or not isinstance(label,str) or not label.strip():raise ValueError('Unique asset id and label required')
        if route not in ('model','generate','kit','reuse','instance','skip'):raise ValueError('Explicit supported route required')
        aids.add(aid);size=vector(source['size_m'],True)
        if not isinstance(instances,list) or not instances:raise ValueError('Explicit instances required')
        members=[]
        for item in instances:
            gid=item['id']
            if not isinstance(gid,str) or not gid or gid in ids:raise ValueError('Unique entity id required')
            ids.add(gid);members.append(gid);location=vector(item['location']);yaw=item.get('yaw_deg',0)
            if type(yaw) not in (int,float) or not math.isfinite(yaw):raise ValueError('Finite yaw required')
            objects.append({'global_id':gid,'name':label+'_'+gid,'asset_id':aid,'parent':item.get('parent'),
                'relation':item.get('relation','on'),'location':location,'rotation_z_deg':yaw,'dimensions_m':size,
                'route':route,'kind':'model' if route in ('model','kit') else 'asset','flags':[], 'order':len(objects)})
        effort=source.get('effort','scene-ready')
        if effort not in ('blockout','scene-ready','hero'):raise ValueError('Unknown effort')
        assets.append({'asset_id':aid,'global_id':members[0],'label':label,'route':route,'route_reason':source.get('reason','explicit design decision'),
            'members':members,'count':len(members),'count_at_least':len(members),'count_at_most':len(members),
            'size_m':size,'size_basis':'design assumption; verify against reference','best_view':None,'source_images':[],
            'flags':[],'effort':effort,'requirements':source.get('requirements',{}),'creation_choice':source.get('creation_choice',{}),
            'description':source.get('description',label)})
    parents={r['global_id']:r.get('parent') for r in [*anchors,*objects]}
    for gid,parent in parents.items():
        if parent is not None and parent not in ids:raise ValueError('Unknown support parent: '+str(parent))
        seen={gid};node=parent
        while node is not None:
            if node in seen:raise ValueError('Support cycle')
            seen.add(node);node=parents[node]
    # A deliberately skipped object cannot silently disappear from a support chain.
    skipped={r['global_id'] for r in objects if r['route']=='skip'}
    if any(parent in skipped for parent in parents.values()):
        raise ValueError('Skipped support parent: provide an existing anchor or include its asset')
    # Preserve explicit decisions without creating counterfeit view/detection data.
    plan={'schema':'marso/asset-plan@1','source_schema':doc['schema'],'run_id':doc['run_id'],'assets':assets,'anchors':anchors,
          'review':doc.get('review',[]),'images':[],'unconfirmed':[]}
    placement={'schema':'marso/placement@1','run_id':doc['run_id'],'project':doc.get('project','Scene'),
               'project_id':doc.get('project_id'),'anchors':[dict(r,name=r.get('name',r['global_id']),kind='support') for r in anchors],
               'objects':[r for r in objects if r['route']!='skip'],'assets':{},'review':[],
               'assumptions':['Explicit designed placement; not a photo reconstruction or geometry approval']}
    return plan,placement


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source');parser.add_argument('--out',required=True);parser.add_argument('--placement',required=True)
    args=parser.parse_args();paths=[Path(args.out),Path(args.placement)]
    if paths[0].resolve()==paths[1].resolve() or any(p.exists() for p in paths):raise ValueError('Use two new output paths; preserve existing decisions')
    outputs=build(json.loads(Path(args.source).read_text(encoding='utf-8')))
    for path,output in zip(paths,outputs):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(output,indent=2),encoding='utf-8')


if __name__=='__main__':main()
