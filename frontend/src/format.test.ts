import {describe,it,expect} from 'vitest';
import {formatMetric} from './format';
describe('honest measurement labels',()=>{
 it('distinguishes missing samples from zero delivery',()=>{
  expect(formatMetric(null,'%')).toBe('—');
  expect(formatMetric(0,'%')).toBe('0%');
  expect(formatMetric(98.2,'%')).toBe('98.2%');
 });
});
