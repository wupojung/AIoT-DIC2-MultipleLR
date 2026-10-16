# Python foundation

Requires Python 3.11+; this foundation is verified on Python 3.14.2. No third-party
dependencies are needed for the environment smoke check. pandas, numpy,
scikit-learn, matplotlib and joblib remain deferred until analysis needs them;
compatibility and versions must be checked when introduced.

From the repository root on macOS:
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python python/src/environment_check.py
python -m unittest discover -s tests -v
```
Windows PowerShell:
```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe python/src/environment_check.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
Choose an installed Python 3.11+ interpreter. Activation is optional when using
its full path. The check prints JSON status PASS and the actual Python version;
it does not validate an ML environment or produce model results.

Future components will follow CRISP-DM: document problem and source, inspect data,
create leakage-safe preprocessing and split, train/evaluate reproducibly, export
reviewed artifacts under outputs/. Their commands and dependencies will be added
with implementation. No analysis command exists yet.
