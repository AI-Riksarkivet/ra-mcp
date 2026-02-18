---
name: release
description: >
  Cut a new release of ra-mcp. Determines the next version from the commit
  history since the last tag, bumps pyproject.toml, commits, tags, and pushes.
  Use when: "make a release", "cut a release", "release", "bump version",
  "tag a new version", "publish a new version".
---

# Release Skill

Cut a new release for the ra-mcp project.

## Workflow

1. **Determine current state** — run these in parallel:
   - `git tag --sort=-v:refname | head -5` to find the latest tag
   - `grep '^version' pyproject.toml | head -1` to find the current version
   - `git log --oneline $(git describe --tags --abbrev=0)..HEAD` to list commits since the last tag

2. **Decide the version bump** — follow semver based on conventional commits:
   - **patch** (0.x.Y): only `fix`, `refactor`, `perf`, `docs`, `style`, `test`, `build`, `ci`, `chore`
   - **minor** (0.X.0): any `feat` commit
   - **major** (X.0.0): any commit with `!` or `BREAKING CHANGE` footer
   - If the user specified a version, use that instead

3. **Confirm with the user** — show:
   - Current version and proposed next version
   - Summary of commits going into the release
   - Ask for approval before proceeding

4. **Cut the release** — run:
   ```bash
   make release VERSION=<version>
   ```
   This bumps `pyproject.toml`, commits, tags, and pushes. The tag push
   triggers two CI workflows in parallel: `release.yml` (changelog + GitHub
   Release) and `publish.yml` (Docker build, push, sign, and attestations).

5. **Monitor CI workflows** — after the tag push, watch both workflows:
   - Run `gh run list --limit 5` to find the triggered runs
   - Poll with `gh run view <run-id>` until both "Release" and "Publish"
     workflows complete (check every ~30 seconds)
   - If either workflow fails, run `gh run view <run-id> --log-failed` to
     get the error details and report them to the user
   - Only proceed to the report step once both workflows succeed

6. **Report** — confirm the tag was pushed and link to the GitHub releases page:
   `https://github.com/AI-Riksarkivet/ra-mcp/releases`

## Rules

- ALWAYS confirm the version with the user before running `make release`
- NEVER skip the confirmation step
- If there are uncommitted changes, warn the user and stop
- If there are no new commits since the last tag, tell the user and stop
- When making any git commits (e.g., committing uncommitted changes before
  releasing), follow the conventions in `.claude/commands/commit.md` —
  in particular: no co-author lines, no Claude attribution, clean
  conventional commit format
