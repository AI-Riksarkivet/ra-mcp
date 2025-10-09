// RA-MCP Dagger CI/CD Pipeline
package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"strings"
)

type RaMcp struct{}

// BuildLocal builds using Dockerfile from a local directory with custom environment variables
func (m *RaMcp) BuildLocal(
	ctx context.Context,
	// Local directory to build from
	// +optional
	source *dagger.Directory,
	// Image repository name
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// Environment variables for build customization (KEY=VALUE format)
	// +default=[]
	envVars []string,
	// Image tag
	// +default="latest"
	imageTag string,
	// Registry URL
	// +default="docker.io"
	registry string,
) (*dagger.Container, error) {
	// Convert environment variables to build args
	var buildArgs []dagger.BuildArg
	buildArgs = append(buildArgs, dagger.BuildArg{Name: "REGISTRY", Value: registry})

	// Parse environment variables and add to build args
	for _, envVar := range envVars {
		if parts := strings.Split(envVar, "="); len(parts) == 2 {
			buildArgs = append(buildArgs, dagger.BuildArg{
				Name:  parts[0],
				Value: parts[1],
			})
		}
	}

	// Build the container using Dockerfile
	container := dag.Container().
		Build(source, dagger.ContainerBuildOpts{
			Dockerfile: "Dockerfile",
			BuildArgs:  buildArgs,
		})

	return container, nil
}

// Build creates a production-ready container image using default settings
func (m *RaMcp) Build(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	source *dagger.Directory,
) (*dagger.Container, error) {
	return m.BuildLocal(ctx, source, "riksarkivet/ra-mcp", []string{}, "latest", "docker.io")
}

// Test runs the test suite using the built container
func (m *RaMcp) Test(
	ctx context.Context,
	// +optional
	source *dagger.Directory,
) (string, error) {
	container, err := m.Build(ctx, source)
	if err != nil {
		return "", err
	}

	return container.
		WithExec([]string{"uv", "run", "pytest", "--cov=src/ra_mcp", "--cov-report=term"}).
		Stdout(ctx)
}

// Publish builds and publishes container image to registry with authentication
func (m *RaMcp) Publish(ctx context.Context,
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// +default="latest"
	tag string,
	// +default="docker.io"
	registry string,
	// Docker username for authentication
	// +default="airiksarkivet"
	dockerUsername string,
	// Docker password from environment variable
	dockerPassword *dagger.Secret,
	// +optional
	source *dagger.Directory) (string, error) {

	container, err := m.Build(ctx, source)
	if err != nil {
		return "", err
	}

	imageRef := registry + "/" + imageRepository + ":" + tag

	// Authenticate with Docker registry if credentials provided
	if dockerPassword != nil && dockerUsername != "" {
		return container.
			WithRegistryAuth(registry, dockerUsername, dockerPassword).
			Publish(ctx, imageRef)
	}

	return container.Publish(ctx, imageRef)
}
