# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-08-25

Full-repository audit pass: documentation accuracy, workflow hardening, and lint hygiene.

### ✨ Added

- **pyproject.toml** - committed ruff lint configuration (`line-length = 120`, E/F/W/B rules)

### 🔧 Changed

- **Workflows hardened** - all GitHub Actions pinned to exact commit SHAs instead of moving major tags:
  - `actions/checkout@v4.4.0`
  - `actions/setup-python@v5.6.0` (plus pip dependency caching)
  - `stefanzweifel/git-auto-commit-action@v5.2.0`
  - `actions/first-interaction@v1.3.0`
- **LICENSE** - copyright year extended through 2026
- **FUNDING.yml** - removed dead Patreon handle; Ko-fi retained (verified live)
- **greetings.yml** - quoted `"on":` key for YAML style consistency with the other workflow

### 🐛 Fixed

- **QUICKSTART.md** - rewritten to describe the current repository (was still documenting the retired snake-animation / metrics-workflow setup under the old repo name)
- **CONTRIBUTING.md** - clone instructions pointed at the old repository name; now follows the fork-then-clone-your-fork flow
- **greetings.yml** - welcome message linked a relative README path that does not resolve in issue comments
- **make_wordmark_svg.py** - corrected misleading docstring claim about CSS animation support in GitHub's `<img>` sandbox
- **scripts/** - resolved all ruff findings (ambiguous variable name, over-long line, unused loop variable)

### 🧹 Removed

- **assets/** - unused placeholder directory whose README described subdirectories that never existed

## [2.0.0] - 2025-10-31

### 🎉 Major Overhaul

This release represents a complete transformation of the profile repository with professional structure and comprehensive features.

### ✨ Added

#### Documentation
- **LICENSE** - MIT License for open-source contributions
- **SECURITY.md** - Security policy and vulnerability reporting guidelines
- **CONTRIBUTING.md** - Comprehensive contribution guidelines
- **CODE_OF_CONDUCT.md** - Community standards and expectations
- **CHANGELOG.md** - Version history tracking (this file!)
- **.gitignore** - Comprehensive gitignore for multiple languages

#### Documentation
- **Issue Templates** - Bug report and feature request templates
- **PR Template** - Standardized pull request template
- **FUNDING.yml** - GitHub Sponsors configuration
- **Improved Workflows:**
  - Enhanced `main.yml` with error handling and concurrency control
  - `profile-update.yml` - Daily stats update automation
  - `metrics.yml` - Weekly repository metrics tracking

#### README Enhancements
- **Table of Contents** - Easy navigation
- **About Me section** - Detailed introduction with current focus
- **Achievements section** - Expanded accomplishments list
- **Enhanced Contact section** - Professional call-to-action with badges
- **Workflow status badge** - Real-time CI/CD status
- **License badge** - MIT license indicator

### 🐛 Fixed
- Typo: "Developement" → "Development"
- `<picture>` element: Fixed duplicate dark mode source (now properly supports light/dark)

### 🔧 Improved
- Snake animation workflow with better error handling
- Concurrency control to prevent workflow conflicts
- Step naming for better workflow readability
- README organization and visual hierarchy
- Professional tone and presentation throughout

## [1.0.0] - 2024-XX-XX

### Initial Release
- Basic README with bio and tech stack
- Social links (LinkedIn, Email)
- GitHub stats and badges
- Snake animation workflow
- Tech stack badges

---

## Template for Future Releases

## [Unreleased]

### Added
- New features in development

### Changed
- Updates to existing features

### Deprecated
- Features being phased out

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security updates

---

**Note:** Dates follow YYYY-MM-DD format. Version numbers follow semantic versioning (MAJOR.MINOR.PATCH).
