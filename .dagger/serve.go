package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// Serve starts the RA-MCP server as a service
func (m *RaMcp) Serve(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Port to expose the service on
	// +default=7860
	port int,
	// Host to bind to (0.0.0.0 for all interfaces, 127.0.0.1 for localhost only)
	// +default="0.0.0.0"
	host string,
) (*dagger.Service, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, err
	}

	return container.
		WithExposedPort(port).
		AsService(dagger.ContainerAsServiceOpts{
			Args: []string{
				"ra", "serve",
				"--host", host,
				"--port", fmt.Sprintf("%d", port),
			},
		}), nil
}
