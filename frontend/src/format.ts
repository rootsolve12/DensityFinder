/** Preserve the distinction between no samples and a measured zero. */
export function formatMetric(value:number|null|undefined,unit=''):string {
 return value==null?'—':`${value}${unit}`;
}
