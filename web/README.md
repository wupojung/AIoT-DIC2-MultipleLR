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
It checks HTTP and direct-file opening at 1920×1080, 1440×900, 768×1024,
390×844 and 375×812; all tabs and button states, keyboard navigation, text
overflow, horizontal scrolling and browser console/page/network errors.
It writes 15 actual full-page PNG captures and verification.json under
docs/screenshots/. See the [verification evidence](../docs/screenshots/README.md).
Playwright is installed outside the project solely for verification, not shipped
with the dashboard. Windows/browser automation is not yet verified.
