# Pinned browser numerical/CSV dependencies

`numerics.mjs` is a locally served ES-module bundle, not a CDN dependency:

- [ml-matrix](https://github.com/mljs/matrix) **6.12.1**: SVD least-squares solver, rank/condition diagnostics.
- [Papa Parse](https://github.com/mholt/PapaParse) **5.5.3**: CSV quoting, escaped delimiters and newlines.
- esbuild **0.25.12** was used only to create the bundle; no build tool is loaded by the application.

MIT notices for all bundled packages are preserved in LICENSES.txt. The lockfile records exact build dependencies/integrities; it is not user data.

Rebuild in a temporary directory, with Node/npm available:

```sh
mkdir -p /tmp/mlr-vendor
cp web/vendor/build-package.json /tmp/mlr-vendor/package.json
cp web/vendor/build-lock.json /tmp/mlr-vendor/package-lock.json
npm ci --prefix /tmp/mlr-vendor
```

Create `/tmp/mlr-vendor/entry.js`:

```js
export {Matrix, SingularValueDecomposition} from 'ml-matrix';
import Papa from 'papaparse';
export const parseCSV = Papa.parse;
```

```sh
/tmp/mlr-vendor/node_modules/.bin/esbuild /tmp/mlr-vendor/entry.js --bundle --format=esm --minify --legal-comments=inline --outfile=web/vendor/numerics.mjs
node --test tests/custom_engine.test.mjs
```

`npm` installation is unnecessary for normal serving or GitHub Pages deployment. Numerical behavior is verified against independently generated sklearn references rather than assumed from library choice.
