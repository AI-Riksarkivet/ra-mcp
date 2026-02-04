// RA-MCP Dagger CI/CD Pipeline
package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
	"strings"
)

// RaMcp provides CI/CD pipeline functions for the RA-MCP project
type RaMcp struct{}

// Default configuration constants
const (
	DefaultRegistry       = "docker.io"
	DefaultImageRepo      = "riksarkivet/ra-mcp"
	DefaultDockerUsername = "airiksarkivet"
	DefaultPyPIURL        = "https://upload.pypi.org/legacy/"
	DefaultPyPIUsername   = "__token__"
)

// withUv adds uv to a container (for development/CI tasks only)
func (m *RaMcp) withUv(container *dagger.Container) *dagger.Container {
	uvBinary := dag.Container().
		From("ghcr.io/astral-sh/uv:latest").
		File("/uv")

	uvxBinary := dag.Container().
		From("ghcr.io/astral-sh/uv:latest").
		File("/uvx")

	return container.
		WithFile("/usr/local/bin/uv", uvBinary).
		WithFile("/usr/local/bin/uvx", uvxBinary)
}

// buildWithUv builds a container and adds uv tooling to it
func (m *RaMcp) buildWithUv(ctx context.Context, source *dagger.Directory) (*dagger.Container, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, err
	}
	return m.withUv(container), nil
}

// getVersion retrieves the raw version from pyproject.toml using uv
func (m *RaMcp) getVersion(ctx context.Context, source *dagger.Directory) (string, error) {
	// Use a builder container with source files (not the production image)
	container := dag.Container().
		From("python:3.12-alpine").
		WithDirectory("/app", source).
		WithWorkdir("/app")

	container = m.withUv(container)

	version, err := container.
		WithExec([]string{"uv", "version", "--short"}).
		Stdout(ctx)

	if err != nil {
		return "", err
	}

	return strings.TrimSpace(version), nil
}

// validateVersion checks if the provided tag matches the version in pyproject.toml
func (m *RaMcp) validateVersion(ctx context.Context, source *dagger.Directory, tag string) error {
	projectVersion, err := m.getVersion(ctx, source)
	if err != nil {
		return fmt.Errorf("failed to get version from pyproject.toml: %w", err)
	}

	normalizeVersion := func(v string) string {
		return strings.TrimPrefix(strings.TrimSpace(v), "v")
	}

	normalizedProject := normalizeVersion(projectVersion)
	normalizedTag := normalizeVersion(tag)

	if normalizedProject != normalizedTag {
		return fmt.Errorf(
			"version mismatch: pyproject.toml has version 'v%s' but release tag is '%s'",
			projectVersion,
			tag,
		)
	}

	return nil
}
