# `.claude/` Directory

Project-level configuration for Claude Code. Everything here is git-tracked and available to anyone who clones the repo.

## What This Directory Contains

| Path | Purpose |
|---|---|
| `settings.json` | Project settings (enabled plugins, permissions, etc.) |
| `skills/` | Local skills — context documents that Claude loads on demand |
| `commands/` | Slash commands (`/commit`, etc.) |

## Skills

Skills are markdown files (`SKILL.md`) that teach Claude how to handle specific tasks. Each skill lives in its own subdirectory under `.claude/skills/`.

```
.claude/skills/
  ra-mcp-apps/SKILL.md
  testing-python/SKILL.md
  ...
```

A skill's YAML frontmatter includes a `description` field that tells Claude when to activate it. When a user's request matches the description, Claude loads the skill automatically.

Because skills live in the repo, they're available to every contributor on clone — no extra installation needed.

## Plugins (External Skills)

Plugins are third-party skill packages installed separately. They're enabled in `settings.json` under `enabledPlugins`:

```json
{
  "enabledPlugins": {
    "svelte-skills@svelte-skills-kit": true,
    "toolkit-skills@claude-code-toolkit": true
  }
}
```

To install a plugin:

```bash
claude plugin install <package-name>
```

Enabling a plugin in `settings.json` makes it available for the project, but each developer still needs to install the plugin package locally.

## Commands

Custom slash commands live in `.claude/commands/`. Each `.md` file becomes a command named after the file (e.g., `commit.md` provides `/commit`).

Commands are prompts that get expanded when invoked — useful for standardizing workflows like commit messages, code review, or scaffolding.

## Monorepo Note

Claude resolves `.claude/` from the project root. In a monorepo with multiple packages, keep a single `.claude/` at the root. If a sub-package needs its own configuration, symlink from the sub-package into the root `.claude/` directory.
