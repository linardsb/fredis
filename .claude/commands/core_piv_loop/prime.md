 ---
description: Prime agent with codebase understanding
---

# Prime: Load Project Context

## Objective

Build comprehensive understanding of the codebase by analyzing structure, documentation, and key files.

## Process

### 1. Analyze Project Structure

Detect if this is a git repo:
!`git rev-parse --is-inside-work-tree 2>/dev/null && echo "GIT_REPO=yes" || echo "GIT_REPO=no"`

**If git repo (`GIT_REPO=yes`)** — list tracked files:
!`git ls-files 2>/dev/null | head -200`

**If not a git repo (`GIT_REPO=no`)** — list files via the Glob tool (pattern `**/*`) or fall back to:
!`find . -type f -not -path '*/node_modules/*' -not -path '*/__pycache__/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.venv/*' | head -200`

Show directory structure (works in both modes):
!`command -v tree >/dev/null && tree -L 3 -I 'node_modules|__pycache__|.git|dist|build|.venv' || find . -maxdepth 3 -type d -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*'`

### 2. Read Core Documentation

- Read CLAUDE.md or similar global rules file
- Read README files at project root and major directories
- Read any architecture documentation

### 3. Identify Key Files

Based on the structure, identify and read:
- Main entry points (main.py, index.ts, app.py, etc.)
- Core configuration files (pyproject.toml, package.json, tsconfig.json)
- Key model/schema definitions
- Important service or controller files

### 4. Understand Current State

**If git repo** — check recent activity and status:
!`git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git log -10 --oneline || echo "(not a git repo — skipping git log)"`

!`git rev-parse --is-inside-work-tree >/dev/null 2>&1 && git status || echo "(not a git repo — skipping git status)"`

**If not a git repo** — inspect filesystem activity instead:
!`find . -type f -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/__pycache__/*' -not -path '*/.venv/*' -mtime -14 -printf '%TY-%Tm-%Td %TH:%TM  %p\n' 2>/dev/null | sort -r | head -20`

Also check for nested git repos (sub-vaults, synced folders):
!`find . -maxdepth 4 -name '.git' -type d 2>/dev/null`

## Output Report

Provide a concise summary covering:

### Project Overview
- Purpose and type of application
- Primary technologies and frameworks
- Current version/state

### Architecture
- Overall structure and organization
- Key architectural patterns identified
- Important directories and their purposes

### Tech Stack
- Languages and versions
- Frameworks and major libraries
- Build tools and package managers
- Testing frameworks

### Core Principles
- Code style and conventions observed
- Documentation standards
- Testing approach

### Current State
- Active branch
- Recent changes or development focus
- Any immediate observations or concerns

**Make this summary easy to scan - use bullet points and clear headers.**
