import { readFile } from 'node:fs/promises';
import { access } from 'node:fs/promises';

const source = await readFile(new URL('../slides.md', import.meta.url), 'utf8');
const slides = source.split(/^---$/m).filter((part) => part.includes('\n#'));
const required = [
  'Research to POCs',
  '63 PRs total',
  '43 merged',
  '20 open',
  'AAIF project proposal #26',
  'not an adopted architecture',
  'one implementation under discussion',
  'https://cloudfoundry.github.io/agentic-runtime-notes/',
];

if (slides.length !== 11) throw new Error(`expected 11 slides, found ${slides.length}`);

for (const text of required) {
  if (!source.includes(text)) throw new Error(`missing required text: ${text}`);
}

// Every slide needs a speaker note: an HTML comment that is not a Marp directive.
const withoutNotes = slides
  .map((slide, index) => ({ slide, index }))
  .filter(({ slide }) => !/<!--(?!\s*_)/.test(slide))
  .map(({ index }) => index + 1);
if (withoutNotes.length > 0) {
  throw new Error(`slides missing speaker notes: ${withoutNotes.join(', ')}`);
}

if (/rabobank|TODO|TBD|FIXME/i.test(source)) {
  throw new Error('forbidden branding or unresolved placeholder found');
}

// The theme must stay on the cloudfoundry.org palette, not Pivotal teal.
const theme = await readFile(new URL('../theme/cloud-foundry.css', import.meta.url), 'utf8');
for (const banned of ['#18a999', '#0f7c90', '#ef8354']) {
  if (theme.includes(banned)) throw new Error(`off-brand colour in theme: ${banned}`);
}
if (!theme.includes('#0c9ed5')) throw new Error('theme is missing the Cloud Foundry primary blue');

// Every referenced image must exist next to the deck, and must also be copied
// into build/ — Marp resolves image URLs relative to the *output* file.
const images = [
  ...source.matchAll(/!\[[^\]]*\]\(([^)]+)\)/g),
  ...source.matchAll(/<img\b[^>]*\bsrc="([^"]+)"[^>]*>/g),
].map((m) => m[1]);
if (images.length === 0) throw new Error('expected at least one image in the deck');
for (const image of images) {
  for (const base of ['..', '../build']) {
    const target = new URL(`${base}/${image}`, import.meta.url);
    try {
      await access(target);
    } catch {
      throw new Error(`image "${image}" missing from ${base === '..' ? 'source' : 'build output'}`);
    }
  }
}

console.log(`validated ${slides.length} slides, ${required.length} required claims, ${images.length} images, speaker notes and palette`);
