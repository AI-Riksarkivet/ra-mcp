package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"strings"
)

// parseBuildArgs converts environment variable strings to BuildArg slices
func parseBuildArgs(registry string, envVars []string) []dagger.BuildArg {
	buildArgs := []dagger.BuildArg{{Name: "REGISTRY", Value: registry}}

	for _, envVar := range envVars {
		if parts := strings.Split(envVar, "="); len(parts) == 2 {
			buildArgs = append(buildArgs, dagger.BuildArg{
				Name:  parts[0],
				Value: parts[1],
			})
		}
	}

	return buildArgs
}

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
	// Registry URL
	// +default="docker.io"
	registry string,
) (*dagger.Container, error) {
	buildArgs := parseBuildArgs(registry, envVars)

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
	return m.BuildLocal(ctx, source, DefaultImageRepo, []string{}, DefaultRegistry)
}
