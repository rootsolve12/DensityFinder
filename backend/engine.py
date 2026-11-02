"""Deterministic geometric graph and explicit, simplified radio model."""
import math
import networkx as nx
import numpy as np
from pydantic import BaseModel, Field

class Scenario(BaseModel):
    count: int = Field(50, ge=5, le=150)
    range: float = Field(250, ge=80, le=400)
    seed: int = Field(42, ge=0, le=1000000)
    placement: str = Field('organic', pattern='^(organic|grid|clustered)$')
    environment: str = Field('clear', pattern='^(clear|rain|dense)$')

class Simulation:
    def __init__(self, config=None):
        self.config = config or Scenario()
        self.tick = 0
        self.events = []
        self.comparison = None
        rng = np.random.default_rng(self.config.seed)
        n = self.config.count
        if self.config.placement == 'grid':
            side = math.ceil(math.sqrt(n))
            positions = [(100+800*(i%side)/max(side-1,1),100+800*(i//side)/max(side-1,1)) for i in range(n)]
        elif self.config.placement == 'clustered':
            positions = np.clip(rng.normal(0,95,(n,2)) + np.array([[220,250] if i<n//2 else [790,750] for i in range(n)]),30,970)
        else:
            positions = rng.uniform(45,955,(n,2))
        self.nodes = [dict(id=i,x=round(float(p[0]),2),y=round(float(p[1]),2),active=True,battery=round(float(rng.uniform(55,100)),1),temperature=round(float(rng.normal(25,2)),1),humidity=round(float(rng.uniform(60,85)),1)) for i,p in enumerate(positions)]
        self.gateway = 0

    def graph(self):
        g = nx.Graph()
        active = [n for n in self.nodes if n['active']]
        g.add_nodes_from(n['id'] for n in active)
        radius = self.config.range * {'clear':1,'rain':.85,'dense':.72}[self.config.environment]
        for i,a in enumerate(active):
            for b in active[i+1:]:
                d = math.hypot(a['x']-b['x'],a['y']-b['y'])
                if d <= radius: g.add_edge(a['id'],b['id'],distance=round(d,1))
        return g,radius

    def snapshot(self):
        g,radius = self.graph()
        reachable = nx.node_connected_component(g,self.gateway) if self.gateway in g else set()
        # Fixed cell-center quadrature; coverage is a geometric estimate, not RF measurement.
        axis = np.arange(5,1000,10)
        points = np.stack(np.meshgrid(axis,axis),axis=-1).reshape(-1,2)
        active = [n for n in self.nodes if n['active']]
        covered = np.zeros(len(points),dtype=bool)
        for n in active: covered |= np.sum((points-[n['x'],n['y']])**2,axis=1)<=radius**2
        delivered = [e for e in self.events if e['delivered']]
        metrics = dict(spatial_density=len(active),theoretical_neighbors=round(len(active)*math.pi*(self.config.range/1000)**2,2),coverage=round(float(covered.mean()*100),1),reachable=len(reachable),active=len(active),links=g.number_of_edges(),components=nx.number_connected_components(g),average_degree=round(sum(dict(g.degree()).values())/max(len(g),1),2),battery=round(sum(n['battery'] for n in active)/max(len(active),1),1),pdr=round(100*len(delivered)/len(self.events),1) if self.events else None,latency=round(sum(e['latency'] for e in delivered)/len(delivered),1) if delivered else None,effective_range=radius)
        gaps = points[~covered][::max(1,int((~covered).sum()/120))].tolist()
        return dict(config=self.config.model_dump(),nodes=[dict(n,reachable=n['id'] in reachable,degree=g.degree(n['id']) if n['id'] in g else 0,gateway=n['id']==self.gateway,route=nx.shortest_path(g,n['id'],self.gateway) if n['id'] in reachable else []) for n in self.nodes],edges=[dict(source=a,target=b,**d) for a,b,d in g.edges(data=True)],metrics=metrics,events=self.events[-30:][::-1],comparison=self.comparison,gaps=gaps,tick=self.tick)

    def event(self,node_id=None):
        self.tick += 1
        rng = np.random.default_rng(self.config.seed+self.tick)
        source = int(rng.integers(1,len(self.nodes))) if node_id is None else node_id
        g,_ = self.graph()
        route = nx.shortest_path(g,source,self.gateway) if source in g and self.gateway in g and nx.has_path(g,source,self.gateway) else []
        hops = max(0,len(route)-1)
        # Simulated per-hop loss; reproducible, never presented as field measurements.
        success = bool(route) and bool(rng.random() < (.98 if self.config.environment=='clear' else .92)**hops)
        event = dict(id=self.tick,node=source,kind=str(rng.choice(['Elephant movement','Wildlife crossing','Canopy motion','Deer activity'])),route=route,delivered=success,latency=round(hops*18+float(rng.uniform(4,12)),1) if success else None,hops=hops,time=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),reason='Delivered to gateway' if success else ('No gateway route' if not route else 'Simulated packet loss'))
        self.events.append(event)
        for i in route: self.nodes[i]['battery']=round(max(0,self.nodes[i]['battery']-.02),2)
        return event

    def optimize(self):
        before = self.snapshot()['metrics']
        original = [(n['x'],n['y']) for n in self.nodes]
        # Try regular deployments at several extents; accept only a non-regressing candidate.
        best = original
        score = lambda m: (m['reachable'],m['coverage'], -m['components'])
        best_metrics=before
        side=math.ceil(math.sqrt(len(self.nodes)))
        for extent in [650,750,850]:
            for i,n in enumerate(self.nodes):
                n['x']=round((1000-extent)/2+extent*(i%side)/max(side-1,1),2)
                n['y']=round((1000-extent)/2+extent*(i//side)/max(side-1,1),2)
            m=self.snapshot()['metrics']
            if m['reachable']>=before['reachable'] and m['coverage']>=before['coverage'] and score(m)>score(best_metrics):
                best=[(n['x'],n['y']) for n in self.nodes]; best_metrics=m
        for n,p in zip(self.nodes,best): n['x'],n['y']=p
        self.comparison=dict(before=before,after=best_metrics,moved=sum(a!=b for a,b in zip(original,best)),method='Deterministic grid candidate search; maximize gateway reachability then estimated coverage, without reducing either.')
