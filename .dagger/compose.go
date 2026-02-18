package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// ComposeUp loads the docker-compose.yml and starts the ra-mcp service on the Dagger engine
func (m *RaMcp) ComposeUp(
	// Source directory containing docker-compose.yml and .docker/
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) *dagger.Service {
	project := dag.DockerCompose().Project(dagger.DockerComposeProjectOpts{
		Source: source,
	})
	return project.Service("ra-mcp").Up()
}

// ComposeTest starts the compose service and verifies it passes a health check
func (m *RaMcp) ComposeTest(
	ctx context.Context,
	// Source directory containing docker-compose.yml and .docker/
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (string, error) {
	service := m.ComposeUp(source)

	output, err := dag.Container().
		From("curlimages/curl:latest").
		WithServiceBinding("ra-mcp", service).
		WithExec([]string{
			"curl", "-f", "-s",
			"http://ra-mcp:7860/health",
		}).
		Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("compose health check failed: %w", err)
	}

	return fmt.Sprintf("compose service healthy\n\nResponse:\n%s", output), nil
}
