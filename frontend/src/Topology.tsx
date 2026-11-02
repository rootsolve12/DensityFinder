import {useEffect,useRef} from 'react';
import cytoscape from 'cytoscape';
import type {State} from './types';
export default function Topology({state,selected,onSelect,ranges,links,gaps}:{state:State;selected:number|null;onSelect:(id:number)=>void;ranges:boolean;links:boolean;gaps:boolean}){
 const container=useRef<HTMLDivElement>(null);
 const scale=useRef<HTMLElement>(null);
 const packet=useRef<HTMLDivElement>(null);
 const cy=useRef<cytoscape.Core|null>(null);
 const select=useRef(onSelect); select.current=onSelect;
 useEffect(()=>{
  if(!container.current)return;
  const graph=cytoscape({container:container.current,layout:{name:'preset'},minZoom:.35,maxZoom:3,wheelSensitivity:.2,boxSelectionEnabled:false,style:[
   {selector:'node',style:{'width':17,'height':17,'background-color':'#62dfad','border-width':3,'border-color':'#143e34','label':'data(label)','color':'#b3c7bf','font-size':16,'text-margin-y':8,'text-valign':'bottom','overlay-opacity':0}},
   {selector:'node[?gateway]',style:{'shape':'round-rectangle','width':30,'height':30,'background-color':'#f4c76c','border-color':'#6c5831','border-width':4,'color':'#f4d89c','font-size':12}},
   {selector:'node[!reachable]',style:{'background-color':'#f3a75d','border-color':'#66452e'}},
   {selector:'node[!active]',style:{'background-color':'#71828a','border-color':'#303d43','opacity':.6}},
   {selector:'edge',style:{'width':1,'line-color':'#62dfad','opacity':.20,'curve-style':'straight'}},
   {selector:'.route',style:{'line-color':'#f4cb7a','width':3,'opacity':1,'z-index':10}},
   {selector:'node:selected',style:{'border-color':'#ffffff','border-width':3,'width':17,'height':17}}
  ]});
  graph.on('viewport',()=>{if(scale.current)scale.current.style.width=`${200*graph.zoom()}px`});
  graph.on('tap','node',e=>select.current(Number(e.target.id())));
  cy.current=graph;
  const resize=new ResizeObserver(()=>{graph.resize();graph.fit(undefined,45)});resize.observe(container.current);
  return ()=>{resize.disconnect();graph.destroy()};
 },[]);
 useEffect(()=>{
  const graph=cy.current;if(!graph)return;
  const zoom=graph.zoom(), pan=graph.pan();const initial=graph.nodes().length===0;
  graph.elements().remove();
  graph.add([...state.nodes.map(n=>({group:'nodes' as const,data:{...n,id:String(n.id),label:n.gateway?'GATEWAY':String(n.id+1).padStart(2,'0')},position:{x:n.x,y:n.y},selected:n.id===selected})),...state.edges.map(e=>({group:'edges' as const,data:{id:`${e.source}-${e.target}`,source:String(e.source),target:String(e.target)}}))]);
  graph.edges().style('display',links?'element':'none');
  const route=(selected!==null?state.nodes.find(n=>n.id===selected)?.route:state.events[0]?.route) || [];
  for(let i=1;i<route.length;i++) graph.edges().filter(e=>(Number(e.source().id())===route[i-1]&&Number(e.target().id())===route[i])||(Number(e.target().id())===route[i-1]&&Number(e.source().id())===route[i])).addClass('route');
  graph.nodes().ungrabify();
  if(initial)graph.fit(undefined,45);else {graph.zoom(zoom);graph.pan(pan)}
  if(ranges && selected!==null){const node=graph.getElementById(String(selected));node.style({'underlay-color':'#62dfad','underlay-opacity':.055,'underlay-padding':state.metrics.effective_range,'underlay-shape':'ellipse'})}
 },[state,selected,ranges,links]);
 useEffect(()=>{
  const route=state.events[0]?.route||[];
  const graph=cy.current;let frame=0;const start=performance.now();
  if(!graph||route.length<2||!packet.current)return;
  const animate=(now:number)=>{
   if(!packet.current)return;
   const progress=(now-start)/500;const step=Math.floor(progress);
   if(step>=route.length-1){packet.current.style.opacity='0';return}
   const a=graph.getElementById(String(route[step])).renderedPosition(),b=graph.getElementById(String(route[step+1])).renderedPosition();
   if(!a||!b)return;
   const t=progress-step;packet.current.style.opacity='1';packet.current.style.transform=`translate(${a.x+(b.x-a.x)*t}px,${a.y+(b.y-a.y)*t}px)`;
   frame=requestAnimationFrame(animate);
  };frame=requestAnimationFrame(animate);
  return()=>{cancelAnimationFrame(frame);if(packet.current)packet.current.style.opacity='0'};
 },[state.tick]);
 return <><svg className="terrain" viewBox="0 0 1000 1000" preserveAspectRatio="none"><defs><pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse"><path d="M50 0H0V50" fill="none" stroke="#8aa998" strokeOpacity=".09"/></pattern><pattern id="trees" width="67" height="79" patternUnits="userSpaceOnUse"><path d="m12 15 5-9 5 9h-3l5 8H10l5-8z" fill="#264438" opacity=".5"/><circle cx="49" cy="55" r="8" fill="#254434" opacity=".4"/></pattern><radialGradient id="land"><stop stopColor="#213c30"/><stop offset="1" stopColor="#101e1b"/></radialGradient></defs><rect width="1000" height="1000" fill="url(#land)"/><path d="M-70 330Q200 200 380 390T750 490 1100 630" stroke="#315349" strokeWidth="100" fill="none" opacity=".24"/><path d="M-70 330Q200 200 380 390T750 490 1100 630" stroke="#416b66" strokeWidth="30" fill="none" opacity=".24"/><g fill="none" stroke="#627752" opacity=".13">{[0,1,2,3,4,5].map(i=><path key={i} d={`M${-100+i*35} 950Q${50+i*25} ${80+i*65} 1000 ${100+i*80}`}/>)}</g><rect width="1000" height="1000" fill="url(#trees)"/><rect width="1000" height="1000" fill="url(#grid)"/>{gaps&&state.gaps.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r="15" fill="#f59064" opacity=".12"/>)}</svg><div ref={container} className="topology"/><div ref={packet} className="packet" aria-hidden="true"/><div className="map-coordinates">11° 35′ N &nbsp; 76° 32′ E <span>ILLUSTRATIVE TERRAIN</span></div><div className="compass">N<span>↑</span></div><div className="map-scale"><i ref={scale}/> 200 m</div><div className="map-zoom"><button title="Zoom in" onClick={()=>cy.current?.zoom((cy.current?.zoom()||1)*1.2)}>+</button><button title="Zoom out" onClick={()=>cy.current?.zoom((cy.current?.zoom()||1)/1.2)}>−</button><button title="Fit network" onClick={()=>cy.current?.fit(undefined,45)}>⌖</button></div></>;
}
