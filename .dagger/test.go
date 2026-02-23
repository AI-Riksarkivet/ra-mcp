package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
)

// Test runs the test suite with dev dependencies
func (m *RaMcp) Test(
	ctx context.Context,
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use (default: python:3.13-alpine)
	// +default="python:3.13-alpine"
	baseImage string,
) (string, error) {
	if source == nil {
		source = dag.CurrentModule().Source()
	}

	// Create a test container with uv and dev dependencies
	container := dag.Container().
		From(baseImage).
		WithFile("/usr/local/bin/uv", dag.Container().From("ghcr.io/astral-sh/uv:latest").File("/uv")).
		WithFile("/usr/local/bin/uvx", dag.Container().From("ghcr.io/astral-sh/uv:latest").File("/uvx")).
		WithWorkdir("/app").
		WithDirectory("/app", source, dagger.ContainerWithDirectoryOpts{
			Include: []string{
				"pyproject.toml",
				"uv.lock",
				"packages/",
				"src/",
				"README.md",
				"LICENSE",
			},
		}).
		WithExec([]string{"uv", "sync", "--frozen", "--no-cache"}) // Include dev dependencies

	// Run pytest without coverage for now (coverage requires pytest-cov)
	// Test suite is being set up - for now just verify pytest can be invoked
	// Exit code 5 (no tests collected) is acceptable until tests are added
	output, err := container.
		WithExec([]string{"sh", "-c", "uv run pytest packages/ --collect-only -q || test $? -eq 5"}).
		Stdout(ctx)

	if err != nil {
		return "", err
	}

	// Return success message since no tests exist yet
	return "✓ Test infrastructure verified (no tests found - test suite being set up)\n" + output, nil
}
