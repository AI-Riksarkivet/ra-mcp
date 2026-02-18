package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"strings"
)

// BuildLocal builds using .docker/ra-mcp.dockerfile from a local directory with custom environment variables
func (m *RaMcp) BuildLocal(
	ctx context.Context,
	// Local directory to build from
	// +optional
	source *dagger.Directory,
	// Image repository name
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// Base image for builder and production stages
	// +default="python:3.12-alpine"
	baseImage string,
	// Environment variables for build customization (KEY=VALUE format)
	// +default=[]
	envVars []string,
	// Registry URL
	// +default="docker.io"
	registry string,
) (*dagger.Container, error) {
	// Add BASE_IMAGE to build args
	buildArgs := []dagger.BuildArg{
		{Name: "REGISTRY", Value: registry},
		{Name: "BASE_IMAGE", Value: baseImage},
	}

	// Append any additional environment variables
	for _, envVar := range envVars {
		if parts := strings.Split(envVar, "="); len(parts) == 2 {
			buildArgs = append(buildArgs, dagger.BuildArg{
				Name:  parts[0],
				Value: parts[1],
			})
		}
	}

	container := dag.Container().
		Build(source, dagger.ContainerBuildOpts{
			Dockerfile: ".docker/ra-mcp.dockerfile",
			BuildArgs:  buildArgs,
		})

	return container, nil
}

// Build creates a production-ready container image using default settings
func (m *RaMcp) Build(
	ctx context.Context,
	// Source directory containing .docker/ and application code
	// +defaultPath="/"
	source *dagger.Directory,
	// Base image for builder and production stages
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
) (*dagger.Container, error) {
	if baseImage == "" {
		baseImage = "python:3.12-alpine"
	}
	return m.BuildLocal(ctx, source, DefaultImageRepo, baseImage, []string{}, DefaultRegistry)
}
