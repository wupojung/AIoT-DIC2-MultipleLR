# Static dashboard shell

Open index.html directly, or from the repository root run:
```sh
python3 -m http.server 8000 --directory web
```
Visit http://localhost:8000. Windows may use `py -3` instead of `python3`.
No install/build step or framework is required. Local CSS and JavaScript only.
Tabs switch placeholder panels; the disabled dataset selector lists the approved
50 Startups / Boston Housing / Custom Dataset concept. No metrics or figures exist.

Verify desktop and narrow viewport layouts, tab clicks, arrow/Home/End keyboard
navigation, and the browser console. Python output integration and browser versus
backend CSV execution require later work and a separate ADR. There is no API,
model execution, data integration, CSV import or deployment.

## Optional repeatable browser check

The foundation has no Node runtime dependency. For development verification only,
with Node/npm and Chrome installed, start the HTTP server above, then on macOS:
```sh
npm install --prefix /tmp/dic2-browser playwright
NODE_PATH=/tmp/dic2-browser/node_modules node tests/browser_smoke.cjs
```
Run from repository root. The script defaults to the macOS Chrome executable;
set `CHROME_PATH` to another installed Chrome/Chromium executable if needed.
It checks HTTP and direct-file opening, disabled selector, tabs at 1440/375px,
keyboard navigation, horizontal overflow and browser console/page errors.
Playwright is installed outside the project solely for verification, not shipped
with the dashboard. Windows/browser automation is not yet verified.
