import math
from backend.engine import Simulation, Scenario

def test_baseline_and_reproducibility():
    a,b=Simulation(),Simulation()
    assert a.snapshot()==b.snapshot()
    m=a.snapshot()['metrics']
    assert m['spatial_density']==50
    assert m['theoretical_neighbors']==9.82
    assert m['pdr'] is None
    assert 0<m['coverage']<=100
    assert sum(n['degree'] for n in a.snapshot()['nodes'])==2*m['links']

def test_exact_routes_failures_and_gateway():
    s=Simulation(Scenario(count=5,range=250))
    for n,x in zip(s.nodes,[0,200,400,600,800]): n.update(x=x,y=100)
    assert s.event(4)['route']==[4,3,2,1,0]
    s.nodes[2]['active']=False
    assert s.event(4)['reason']=='No gateway route'
    assert s.snapshot()['metrics']['components']==2
    # Add an alternative relay and demonstrate rerouting.
    s.nodes[3].update(x=380,y=100)
    s.nodes[4].update(x=550,y=100)
    assert s.event(4)['route']==[4,3,1,0]
    s.nodes[0]['active']=False
    assert s.snapshot()['metrics']['reachable']==0

def test_environment_and_optimization():
    s=Simulation(Scenario(placement='clustered',environment='dense'))
    assert s.snapshot()['metrics']['effective_range']==180
    before=s.snapshot()['metrics'];s.optimize();after=s.snapshot()['metrics']
    assert after['coverage']>=before['coverage']
    assert after['reachable']>=before['reachable']
    for n in s.nodes: assert 0<=n['x']<=1000 and 0<=n['y']<=1000

def test_events_repeat_for_same_seed():
    a,b=Simulation(),Simulation()
    for _ in range(10):
        x,y=a.event(),b.event()
        x.pop('time');y.pop('time')
        assert x==y

def test_total_outage_and_restore():
    s=Simulation()
    for n in s.nodes: n['active']=False
    state=s.snapshot()
    assert state['metrics']['coverage']==0
    assert state['metrics']['links']==0
    assert state['metrics']['reachable']==0
    assert state['metrics']['components']==0
    assert all(n['route']==[] for n in state['nodes'])
    s.nodes[0]['active']=True
    assert s.snapshot()['nodes'][0]['route']==[0]
