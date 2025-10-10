package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// RuffFormat formats code using ruff (modifies files)
func (m *RaMcp) RuffFormat(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (*dagger.Directory, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, err
	}

	container = m.withUv(container)

	formattedContainer := container.
		WithExec([]string{"uvx", "ruff", "format", "."})

	return formattedContainer.Directory("/app"), nil
}

// RuffCheck fixes linting issues using ruff (modifies files)
func (m *RaMcp) RuffCheck(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (*dagger.Directory, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, err
	}

	container = m.withUv(container)

	fixedContainer := container.
		WithExec([]string{"uvx", "ruff", "check", "--fix", "."})

	return fixedContainer.Directory("/app"), nil
}

// TypeCheck runs type checking with ty (check only, no modifications)
func (m *RaMcp) TypeCheck(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Ignore errors and return result anyway
	// +optional
	ignoreError bool,
) (string, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return "", err
	}

	container = m.withUv(container)

	out, err := container.
		WithExec([]string{"uvx", "ty", "check"}).
		Stdout(ctx)

	if err != nil && !ignoreError {
		return "", fmt.Errorf("type check failed: %w", err)
	}
	return out, nil
}

// Checks runs all code quality checks: first fixes (format + lint), then verifies all pass
func (m *RaMcp) Checks(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (string, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return "", err
	}

	container = m.withUv(container)

	// Step 1: Apply formatting
	container = container.
		WithExec([]string{"uvx", "ruff", "format", "."})

	// Step 2: Fix linting issues
	container = container.
		WithExec([]string{"uvx", "ruff", "check", "--fix", "."})

	// Step 3: Verify everything passes (format check, lint check, type check)
	_, err = container.
		WithExec([]string{"uvx", "ruff", "format", "--check", "."}).
		WithExec([]string{"uvx", "ruff", "check", "."}).
		WithExec([]string{"uvx", "ty", "check"}).
		Sync(ctx)

	if err != nil {
		return "", fmt.Errorf("checks failed: %w", err)
	}

	return "All checks passed ✅ (after auto-formatting and auto-fixing)", nil
}
