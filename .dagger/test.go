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

	output, err := container.
		WithExec([]string{"uv", "run", "pytest", "--tb=short", "-q"}).
		Stdout(ctx)

	if err != nil {
		return "", err
	}

	return output, nil
}
