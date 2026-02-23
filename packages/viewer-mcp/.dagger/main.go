// RA-MCP Dagger CI/CD Pipeline
package main

import (
	"context"
	"dagger/mcp-apps-ra/internal/dagger"
)

// McpAppsRa provides CI/CD pipeline functions for the MCP Apps RA project
type McpAppsRa struct{}

// Default configuration constants
const (
	DefaultRegistry  = "docker.io"
	DefaultImageRepo = "riksarkivet/mcp-apps-ra"
	DefaultPort      = 3001
)

// Build creates a production-ready container image
func (m *McpAppsRa) Build(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	source *dagger.Directory,
) (*dagger.Container, error) {
	container := dag.Container().
		Build(source, dagger.ContainerBuildOpts{
			Dockerfile: "Dockerfile",
		})

	return container, nil
}

// Serve starts the MCP app as a service
func (m *McpAppsRa) Serve(
	ctx context.Context,
	// Source directory
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Port to expose the service on
	// +default=3001
	port int,
) (*dagger.Service, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, err
	}

	return container.
		WithExposedPort(port).
		AsService(), nil
}
