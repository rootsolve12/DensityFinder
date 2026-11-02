export type Config={count:number;range:number;seed:number;placement:string;environment:string};
export type Sensor={id:number;x:number;y:number;active:boolean;battery:number;temperature:number;humidity:number;reachable:boolean;degree:number;gateway:boolean;route:number[]};
export type Metrics={spatial_density:number;theoretical_neighbors:number;coverage:number;reachable:number;active:number;links:number;components:number;average_degree:number;battery:number;pdr:number|null;latency:number|null;effective_range:number};
export type WildlifeEvent={id:number;node:number;kind:string;route:number[];delivered:boolean;latency:number|null;hops:number;time:string;reason:string};
export type State={config:Config;nodes:Sensor[];edges:{source:number;target:number;distance:number}[];metrics:Metrics;events:WildlifeEvent[];comparison:null|{before:Metrics;after:Metrics;moved:number;method:string};gaps:number[][];tick:number};
