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
