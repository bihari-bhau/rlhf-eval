export const DIMENSIONS: { code: string; label: string; hint: string }[] = [
  { code: 'D1', label: 'README', hint: 'Project has a README file' },
  { code: 'D2', label: 'License', hint: 'LICENSE / LICENCE file present' },
  { code: 'D3', label: 'Tests', hint: 'Test files or test directories detected' },
  { code: 'D4', label: 'CI', hint: '.github/workflows with YAML' },
  { code: 'D5', label: 'Pinned deps', hint: 'Lockfile or requirements present' },
  { code: 'D6', label: 'Style / lint config', hint: 'pyproject, eslint, ruff, etc.' },
  { code: 'D7', label: 'Security doc', hint: 'SECURITY.md (partial credit if missing)' },
  { code: 'D8', label: 'Python docstrings', hint: 'Share of defs with docstrings (Python repos)' },
  { code: 'D9', label: 'Community', hint: 'CONTRIBUTING / Code of Conduct' },
]
