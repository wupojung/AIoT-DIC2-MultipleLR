"""Foundation contract checks; run without third-party dependencies."""
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FoundationTests(unittest.TestCase):
    def test_environment_entry_point(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'python/src/environment_check.py')],
            capture_output=True, text=True, check=True, cwd=ROOT)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS')
        self.assertEqual(json.loads(result.stdout)['python'], sys.version.split()[0])

    def test_required_structure(self):
        required = ['README.md', 'AGENTS.md', '.gitignore', 'requirements.txt',
                    'python/README.md', 'python/src/environment_check.py',
                    'web/README.md', 'web/index.html', 'data/README.md',
                    'outputs/.gitkeep', 'docs/CRISP_DM.md', 'docs/ARCHITECTURE.md',
                    'docs/GLOSSARY.md', 'docs/adr/README.md',
                    'docs/adr/ADR-0001-project-foundation.md']
        for name in required:
            with self.subTest(path=name):
                self.assertTrue((ROOT / name).is_file())

    def test_local_document_links(self):
        # Validate file targets, excluding fenced command/template examples.
        for doc in ROOT.rglob('*.md'):
            if '.venv' in doc.parts or '.git' in doc.parts:
                continue
            content = re.sub(r'```.*?```', '', doc.read_text(), flags=re.S)
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', content):
                if '://' not in link and not link.startswith('#'):
                    with self.subTest(document=str(doc), link=link):
                        self.assertTrue((doc.parent / link.split('#')[0]).exists())


if __name__ == '__main__':
    unittest.main()
