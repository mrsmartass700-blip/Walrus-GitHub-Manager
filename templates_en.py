# -*- coding: utf-8 -*-
"""English templates pushed to GitHub (issue templates, docs, labels).

The UI is in Russian, but EVERYTHING that goes to GitHub is in English.
"""

BUG_REPORT_YML = """name: "Bug Report"
description: "Report a bug to help us improve the project"
title: "[Bug]: "
labels: ["bug", "needs-triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!
  - type: textarea
    id: description
    attributes:
      label: "Bug Description"
      description: "A clear and concise description of what the bug is."
      placeholder: "Tell us what happened..."
    validations:
      required: true
  - type: textarea
    id: steps
    attributes:
      label: "Steps To Reproduce"
      description: "Steps to reproduce the behavior."
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. Scroll down to '...'
        4. See error
    validations:
      required: true
  - type: textarea
    id: expected
    attributes:
      label: "Expected Behavior"
      description: "What did you expect to happen?"
    validations:
      required: true
  - type: textarea
    id: screenshots
    attributes:
      label: "Screenshots / Logs"
      description: "If applicable, add screenshots or log output."
  - type: input
    id: version
    attributes:
      label: "Version"
      description: "Which version of the project are you running?"
      placeholder: "v1.0.0"
  - type: dropdown
    id: os
    attributes:
      label: "Operating System"
      options:
        - Windows
        - macOS
        - Linux
        - Other
    validations:
      required: true
  - type: checkboxes
    id: checks
    attributes:
      label: "Checklist"
      options:
        - label: "I have searched existing issues to avoid duplicates"
          required: true
        - label: "I am running the latest version"
"""

FEEDBACK_YML = """name: "Feedback / Feature Request"
description: "Share your feedback or suggest a new feature"
title: "[Feedback]: "
labels: ["feedback", "enhancement"]
body:
  - type: markdown
    attributes:
      value: |
        We love hearing from you! Your feedback makes this project better.
  - type: dropdown
    id: type
    attributes:
      label: "Feedback Type"
      options:
        - Feature request
        - General feedback
        - Improvement suggestion
        - Praise / Thanks
    validations:
      required: true
  - type: textarea
    id: feedback
    attributes:
      label: "Your Feedback"
      description: "Describe your idea or feedback in detail."
    validations:
      required: true
  - type: textarea
    id: problem
    attributes:
      label: "What problem does this solve?"
      description: "If this is a feature request, what problem would it solve?"
  - type: dropdown
    id: rating
    attributes:
      label: "How would you rate the project overall?"
      options:
        - "⭐⭐⭐⭐⭐ Excellent"
        - "⭐⭐⭐⭐ Good"
        - "⭐⭐⭐ Okay"
        - "⭐⭐ Needs work"
        - "⭐ Poor"
"""

ISSUE_CONFIG_YML = """blank_issues_enabled: false
contact_links:
  - name: "Discussions"
    url: "https://github.com/{owner}/{repo}/discussions"
    about: "Ask questions and discuss ideas with the community"
"""

CONTRIBUTING_MD = """# Contributing

Thank you for considering contributing to this project!

## How to Contribute

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m "Add amazing feature"`
4. **Push** to your branch: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## Reporting Bugs

Please use the **Bug Report** issue template and include as much detail
as possible: steps to reproduce, expected behavior, screenshots and logs.

## Suggesting Features

Use the **Feedback / Feature Request** template. Explain the problem your
idea solves — context helps us prioritize.

## Code Style

- Keep changes focused and small
- Write clear commit messages in English
- Add tests when it makes sense

Thanks! ❤️
"""

CODE_OF_CONDUCT_MD = """# Code of Conduct

## Our Pledge

We as members, contributors, and leaders pledge to make participation in our
community a harassment-free experience for everyone.

## Our Standards

Examples of behavior that contributes to a positive environment:

- Being respectful of differing opinions and experiences
- Giving and gracefully accepting constructive feedback
- Focusing on what is best for the community

Examples of unacceptable behavior:

- Trolling, insulting or derogatory comments
- Public or private harassment
- Publishing others' private information without permission

## Enforcement

Instances of abusive behavior may be reported to the project maintainers.
All complaints will be reviewed and investigated promptly and fairly.
"""

PR_TEMPLATE_MD = """## Description

Please describe your changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Checklist

- [ ] My code follows the project style
- [ ] I have performed a self-review
- [ ] I have added tests where appropriate
- [ ] Documentation has been updated
"""

SECURITY_MD = """# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| latest  | ✅        |

## Reporting a Vulnerability

Please **do not** open a public issue for security problems.
Instead, use GitHub's private vulnerability reporting
("Security" tab → "Report a vulnerability") or contact the maintainers
directly. We aim to respond within 72 hours.
"""

FUNDING_YML = """# Ways to support this project
github: [{owner}]
"""

CHANGELOG_MD = """# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Initial release
"""

EDITORCONFIG = """# EditorConfig — consistent coding styles across editors
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4

[*.{js,ts,json,yml,yaml,html,css}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false
"""

CI_WORKFLOW_YML = """name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Sanity check
        run: python -m compileall .
"""

DEPENDABOT_YML = """version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
"""

CODEOWNERS = """# Default owners for everything in the repo
* @{owner}
"""

BADGES = """![GitHub stars](https://img.shields.io/github/stars/{owner}/{name}?style=flat-square)
![GitHub issues](https://img.shields.io/github/issues/{owner}/{name}?style=flat-square)
![GitHub license](https://img.shields.io/github/license/{owner}/{name}?style=flat-square)
![Last commit](https://img.shields.io/github/last-commit/{owner}/{name}?style=flat-square)
"""

README_TEMPLATE = """# {name}

{description}

## Installation

```bash
git clone https://github.com/{owner}/{name}.git
cd {name}
```

## Usage

Describe how to use the project here.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md)
and use our issue templates for bug reports and feedback.

## License

See [LICENSE](LICENSE) for details.
"""

SCREENSHOTS_SECTION = """
## Screenshots

{images}
"""


def build_readme(name, owner, description, badges=False, image_names=None):
    """Собрать README: бейджи + скриншоты (всё на английском)."""
    parts = [f"# {name}\n"]
    if badges:
        parts.append(BADGES.format(owner=owner, name=name))
    parts.append(f"\n{description or 'Project description goes here.'}\n")
    if image_names:
        imgs = "\n".join(
            f'![Screenshot {i + 1}](docs/images/{n})'
            for i, n in enumerate(image_names))
        parts.append(SCREENSHOTS_SECTION.format(images=imgs))
    parts.append(f"""
## Installation

```bash
git clone https://github.com/{owner}/{name}.git
cd {name}
```

## Usage

Describe how to use the project here.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md)
and use our issue templates for bug reports and feedback.

## License

See [LICENSE](LICENSE) for details.
""")
    return "".join(parts)


def screenshots_markdown(image_names):
    imgs = "\n".join(f'![Screenshot {i + 1}](docs/images/{n})'
                     for i, n in enumerate(image_names))
    return SCREENSHOTS_SECTION.format(images=imgs)

# Nice label set (name, color, description) — created in the repo
LABELS = [
    ("bug",            "d73a4a", "Something isn't working"),
    ("enhancement",    "a2eeef", "New feature or request"),
    ("feedback",       "7057ff", "User feedback"),
    ("needs-triage",   "ededed", "Needs review by maintainers"),
    ("documentation",  "0075ca", "Improvements or additions to documentation"),
    ("good first issue", "7cfc00", "Good for newcomers"),
    ("help wanted",    "008672", "Extra attention is needed"),
    ("priority: high", "ff6b6b", "High priority"),
    ("priority: low",  "c2f0c2", "Low priority"),
    ("wontfix",        "ffffff", "This will not be worked on"),
]
