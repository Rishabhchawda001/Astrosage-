// Copy build static assets into the standalone output directory so the
// production standalone server can serve /_next/static/* without Docker.
import { cpSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = dirname(fileURLToPath(import.meta.url)) + '/..';
const src = join(root, '.next/static');
const dest = join(root, '.next/standalone/.next/static');

if (!existsSync(src)) {
  console.error('No .next/static found — run `next build` first.');
  process.exit(1);
}

mkdirSync(dirname(dest), { recursive: true });
cpSync(src, dest, { recursive: true });
console.log('Copied static assets -> .next/standalone/.next/static');
