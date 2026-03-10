# ainur

Local workspace for Ainur/OpenClaw-related agents, notes, handoff files, and market research utilities.

## Repository layout

- `agent/`: local agent implementations
- `hibor/`: Hibor query client code used in this workspace
- `docs/`: notes, reverse-engineering writeups, and handoff artifacts
- `listed-company-research/`: local research skill material
- `pai/`: local market app code
- `tradingagents/`: trading/research agent modules

## Prerequisites

- macOS or a Unix-like shell environment
- `git`
- `python3`
- `gh` if you want GitHub-based sync

## Clone this repository

```bash
git clone https://github.com/leadto818/ainur.git
cd ainur
```

## Sync this repository

Pull the latest changes:

```bash
git pull origin main
```

Push your local changes:

```bash
git add .
git commit -m "Describe your change"
git push origin main
```

## GitHub auth setup

If the local machine has not been linked to GitHub yet:

```bash
gh auth login
gh auth setup-git
```

Optional local Git identity for this repo:

```bash
git config user.name "leadto818"
git config user.email "142968843+leadto818@users.noreply.github.com"
```

## Install the portable skill pack

The four portable skills live in a separate repository:

- [leadto818/openclaw-skills](https://github.com/leadto818/openclaw-skills)

Install them into `~/.codex/skills`:

```bash
git clone https://github.com/leadto818/openclaw-skills.git
cd openclaw-skills
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}" ./install.sh
```

Update them later:

```bash
cd openclaw-skills
git pull origin main
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}" ./install.sh
```

Included skills:

- `warrenq`
- `shiguang`
- `iwencai-browser-api`
- `hibor`

## Offline backup

This repo can also be exported as a Git bundle when needed:

```bash
git bundle create exports/ainur-main.bundle --all
```

An existing exported bundle is available at:

- [ainur-main-20260310.bundle](/Users/yannian/ainur/exports/ainur-main-20260310.bundle)

## Notes

- `exports/` is ignored by Git and is intended for generated archives and transfer artifacts.
- `iwencai/` is currently treated as a separate nested repository and is ignored by the top-level repo.
