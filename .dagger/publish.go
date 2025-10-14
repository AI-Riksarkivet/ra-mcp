package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// testAndBuild runs tests and builds the container if tests pass
func (m *RaMcp) testAndBuild(ctx context.Context, source *dagger.Directory, operation string) (*dagger.Container, error) {
	_, err := m.Test(ctx, source)
	if err != nil {
		return nil, fmt.Errorf("tests failed, aborting %s: %w", operation, err)
	}

	container, err := m.Build(ctx, source)
	if err != nil {
		return nil, fmt.Errorf("build failed during %s: %w", operation, err)
	}

	return container, nil
}

// PublishDocker builds, tests, and publishes container image to registry with authentication
func (m *RaMcp) PublishDocker(
	ctx context.Context,
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// Image tag (if empty, will use version from pyproject.toml with "v" prefix)
	// +optional
	tag string,
	// +default="docker.io"
	registry string,
	// Docker username for authentication
	// +default="airiksarkivet"
	dockerUsername string,
	// Docker password from environment variable
	dockerPassword *dagger.Secret,
	// +optional
	source *dagger.Directory,
	// Skip version validation (not recommended for releases)
	// +optional
	skipValidation bool,
) (string, error) {
	if tag == "" {
		version, err := m.getVersion(ctx, source)
		if err != nil {
			return "", err
		}
		tag = "v" + version
	} else if !skipValidation {
		if err := m.validateVersion(ctx, source, tag); err != nil {
			return "", err
		}
	}

	container, err := m.testAndBuild(ctx, source, "Docker publish")
	if err != nil {
		return "", err
	}

	imageRef := registry + "/" + imageRepository + ":" + tag

	if dockerPassword != nil && dockerUsername != "" {
		return container.
			WithRegistryAuth(registry, dockerUsername, dockerPassword).
			Publish(ctx, imageRef)
	}

	return container.Publish(ctx, imageRef)
}

// PublishPypi builds, tests, and publishes the Python package to PyPI
func (m *RaMcp) PublishPypi(
	ctx context.Context,
	// Source directory containing pyproject.toml
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// PyPI repository URL (for custom registries)
	// +default="https://upload.pypi.org/legacy/"
	publishUrl string,
	// PyPI username (use __token__ for token-based auth)
	// +default="__token__"
	username string,
	// PyPI token or password
	pypiToken *dagger.Secret,
	// Extra arguments for uv build command
	// +optional
	buildArgs []string,
) (string, error) {
	container, err := m.testAndBuild(ctx, source, "PyPI publish")
	if err != nil {
		return "", err
	}

	container = m.withUv(container)

	buildCmd := []string{"uv", "build"}
	buildCmd = append(buildCmd, buildArgs...)

	return container.
		WithExec(buildCmd).
		WithSecretVariable("UV_PUBLISH_PASSWORD", pypiToken).
		WithExec([]string{
			"uv", "publish",
			"--publish-url", publishUrl,
			"--username", username,
		}).
		Stdout(ctx)
}
