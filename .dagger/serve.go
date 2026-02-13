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
	container, err := m.Build(ctx, source, "")
	if err != nil {
		return nil, err
	}

	return container.
		WithExposedPort(port).
		AsService(dagger.ContainerAsServiceOpts{
			Args: []string{
				"ra-serve",
				"--http",
				"--host", host,
				"--port", fmt.Sprintf("%d", port),
			},
		}), nil
}

// TestServer builds and starts the server, then runs a health check
func (m *RaMcp) TestServer(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Port to expose the service on
	// +default=7860
	port int,
) (string, error) {
	// Start the service
	service, err := m.Serve(ctx, source, port, "0.0.0.0")
	if err != nil {
		return "", fmt.Errorf("failed to start service: %w", err)
	}

	// Create a test container to check the service
	endpoint := fmt.Sprintf("http://localhost:%d", port)

	testContainer := dag.Container().
		From("curlimages/curl:latest").
		WithServiceBinding("ra-mcp", service).
		WithExec([]string{
			"curl", "-f", "-s",
			fmt.Sprintf("http://ra-mcp:%d/", port),
		})

	output, err := testContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("health check failed: %w", err)
	}

	return fmt.Sprintf("✅ Server started successfully at %s\n\nResponse:\n%s", endpoint, output), nil
}

// ServeUp builds and exposes the server on the host for manual testing
func (m *RaMcp) ServeUp(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Port to expose on host
	// +default=7860
	port int,
) (*dagger.Service, error) {
	service, err := m.Serve(ctx, source, port, "0.0.0.0")
	if err != nil {
		return nil, err
	}

	// Expose the service port to the host
	return service, nil
}

// ServePublished runs a published Docker image from a registry
func (m *RaMcp) ServePublished(
	ctx context.Context,
	// Docker image reference (e.g., "riksarkivet/ra-mcp:v0.2.3-alpine")
	// +default="riksarkivet/ra-mcp:latest"
	imageRef string,
	// Port to expose
	// +default=7860
	port int,
) (*dagger.Service, error) {
	return dag.Container().
		From(imageRef).
		WithExposedPort(port).
		AsService(dagger.ContainerAsServiceOpts{
			Args: []string{
				"ra-serve",
				"--http",
				"--host", "0.0.0.0",
				"--port", fmt.Sprintf("%d", port),
			},
		}), nil
}

// TestPublished tests a published Docker image from a registry
func (m *RaMcp) TestPublished(
	ctx context.Context,
	// Docker image reference
	// +default="riksarkivet/ra-mcp:latest"
	imageRef string,
	// Port to test
	// +default=7860
	port int,
) (string, error) {
	service, err := m.ServePublished(ctx, imageRef, port)
	if err != nil {
		return "", fmt.Errorf("failed to start published image: %w", err)
	}

	endpoint := fmt.Sprintf("http://localhost:%d", port)

	testContainer := dag.Container().
		From("curlimages/curl:latest").
		WithServiceBinding("ra-mcp", service).
		WithExec([]string{
			"curl", "-f", "-s",
			fmt.Sprintf("http://ra-mcp:%d/", port),
		})

	output, err := testContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("health check failed: %w", err)
	}

	return fmt.Sprintf("✅ Published image %s works!\n\nServer at %s\n\nResponse preview:\n%s",
		imageRef, endpoint, output[:500]+"..."), nil
}
