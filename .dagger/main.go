// RA-MCP Dagger CI/CD Pipeline
package main

import (
	"context"
	"strings"
)

type RaMcp struct{}

// BuildLocal builds using Dockerfile from a local directory with custom environment variables
func (m *RaMcp) BuildLocal(
	ctx context.Context,
	// Local directory to build from
	// +default="."
	source *Directory,
	// Image repository name
	// +default="ra-mcp"
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
) (*Container, error) {
	// Convert environment variables to build args
	var buildArgs []BuildArg
	buildArgs = append(buildArgs, BuildArg{Name: "REGISTRY", Value: registry})

	// Parse environment variables and add to build args
	for _, envVar := range envVars {
		if parts := strings.Split(envVar, "="); len(parts) == 2 {
			buildArgs = append(buildArgs, BuildArg{
				Name:  parts[0],
				Value: parts[1],
			})
		}
	}

	// Build the container using Dockerfile
	container := dag.Container().
		Build(source, ContainerBuildOpts{
			Dockerfile: "Dockerfile",
			BuildArgs:  buildArgs,
		})

	return container, nil
}

// Build creates a production-ready container image using default settings
func (m *RaMcp) Build(ctx context.Context) (*Container, error) {
	return m.BuildLocal(ctx, dag.Host().Directory("."), "ra-mcp", []string{}, "latest", "docker.io")
}

// Test runs the test suite using the built container
func (m *RaMcp) Test(ctx context.Context) (string, error) {
	container, err := m.Build(ctx)
	if err != nil {
		return "", err
	}

	return container.
		WithExec([]string{"uv", "run", "pytest", "--cov=src/ra_mcp", "--cov-report=term"}).
		Stdout(ctx)
}

// Lint checks code quality and formatting using the built container
func (m *RaMcp) Lint(ctx context.Context) (string, error) {
	container, err := m.Build(ctx)
	if err != nil {
		return "", err
	}

	return container.
		WithExec([]string{"uv", "run", "ruff", "check", "src/"}).
		WithExec([]string{"uv", "run", "ruff", "format", "--check", "src/"}).
		Stdout(ctx)
}

// Publish builds and publishes container image to registry
func (m *RaMcp) Publish(ctx context.Context,
	// +default="ra-mcp"
	imageRepository string,
	// +default="latest"
	tag string,
	// +default="docker.io"
	registry string) (string, error) {
	container, err := m.Build(ctx)
	if err != nil {
		return "", err
	}

	imageRef := registry + "/" + imageRepository + ":" + tag
	return container.Publish(ctx, imageRef)
}