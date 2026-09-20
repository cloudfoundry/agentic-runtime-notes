import { readFile } from 'node:fs/promises';

const source = await readFile(new URL('../slides.md', import.meta.url), 'utf8');
const slides = source.split(/^---$/m).filter((part) => part.includes('\n#'));
const required = [
  'Research to POCs',
  '63 PRs total',
  '43 merged',
  '20 open',
  'AAIF project proposal #26',
  'not an adopted architecture',
  'Demo placeholder',
];

if (slides.length !== 10) throw new Error(`expected 10 slides, found ${slides.length}`);
for (const text of required) {
  if (!source.includes(text)) throw new Error(`missing required text: ${text}`);
}
if ((source.match(/<!--/g) ?? []).length !== 11) {
  throw new Error('expected speaker notes on all 10 slides plus the title directive');
}
if (/rabobank|TODO|TBD|FIXME/i.test(source)) {
  throw new Error('forbidden branding or unresolved placeholder found');
}

console.log(`validated ${slides.length} slides and ${required.length} required claims`);
