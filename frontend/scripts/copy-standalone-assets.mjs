// Copy build static assets AND public files into the standalone output
// directory so the production standalone server can serve everything.
import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url)) + '/..';

// Copy .next/static -> .next/standalone/.next/static
const src = join(root, '.next/static');
const dest = join(root, '.next/standalone/.next/static');

if (!existsSync(src)) {
  console.error('No .next/static found — run `next build` first.');
  process.exit(1);
}

mkdirSync(dirname(dest), { recursive: true });
cpSync(src, dest, { recursive: true });
console.log('Copied static assets -> .next/standalone/.next/static');

// Copy public/ -> .next/standalone/public/
const pubSrc = join(root, 'public');
const pubDest = join(root, '.next/standalone/public');

if (existsSync(pubSrc)) {
  mkdirSync(pubDest, { recursive: true });
  cpSync(pubSrc, pubDest, { recursive: true });
  console.log('Copied public files -> .next/standalone/public/');
}
