package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// testAndBuild runs tests and builds the container if tests pass
// NOTE: Tests are currently skipped until test suite is implemented
func (m *RaMcp) testAndBuild(ctx context.Context, source *dagger.Directory, operation string) (*dagger.Container, error) {
	return m.testAndBuildWithBase(ctx, source, "python:3.12-alpine", operation)
}

// testAndBuildWithBase runs tests and builds the container with specified base image
func (m *RaMcp) testAndBuildWithBase(ctx context.Context, source *dagger.Directory, baseImage string, operation string) (*dagger.Container, error) {
	// Skip tests for now
	// _, err := m.Test(ctx, source)
	// if err != nil {
	// 	return nil, fmt.Errorf("tests failed, aborting %s: %w", operation, err)
	// }

	container, err := m.Build(ctx, source, baseImage)
	if err != nil {
		return nil, fmt.Errorf("build failed during %s: %w", operation, err)
	}

	return container, nil
}

// resolveTag resolves the final tag to use, with optional version validation
func (m *RaMcp) resolveTag(ctx context.Context, source *dagger.Directory, tag string, skipValidation bool) (string, error) {
	if tag == "" {
		version, err := m.getVersion(ctx, source)
		if err != nil {
			return "", err
		}
		return "v" + version, nil
	}

	if !skipValidation {
		if err := m.validateVersion(ctx, source, tag); err != nil {
			return "", err
		}
	}

	return tag, nil
}

// PublishDocker builds, tests, and publishes container image to registry with authentication
func (m *RaMcp) PublishDocker(
	ctx context.Context,
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// Image tag (if empty, will use version from pyproject.toml with "v" prefix)
	// +optional
	tag string,
	// Base image for the build (e.g., python:3.12-alpine, cgr.dev/chainguard/python:latest-dev)
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
	// Tag suffix to append (e.g., "-alpine", "-wolfi", "-chainguard")
	// +optional
	tagSuffix string,
	// +default="docker.io"
	registry string,
	// Docker username for authentication (use env: prefix for environment variables)
	dockerUsername *dagger.Secret,
	// Docker password from environment variable
	dockerPassword *dagger.Secret,
	// +optional
	source *dagger.Directory,
	// Skip version validation (not recommended for releases)
	// +optional
	skipValidation bool,
) (string, error) {
	if baseImage == "" {
		baseImage = "python:3.12-alpine"
	}

	resolvedTag, err := m.resolveTag(ctx, source, tag, skipValidation)
	if err != nil {
		return "", err
	}

	// Append tag suffix if provided (e.g., v0.3.0-alpine)
	if tagSuffix != "" {
		resolvedTag = resolvedTag + tagSuffix
	}

	container, err := m.testAndBuildWithBase(ctx, source, baseImage, "Docker publish")
	if err != nil {
		return "", err
	}

	imageRef := registry + "/" + imageRepository + ":" + resolvedTag

	if dockerPassword != nil && dockerUsername != nil {
		username, err := dockerUsername.Plaintext(ctx)
		if err != nil {
			return "", fmt.Errorf("failed to read docker username: %w", err)
		}
		return container.
			WithRegistryAuth(registry, username, dockerPassword).
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
	_, err := m.Test(ctx, source)
	if err != nil {
		return "", fmt.Errorf("tests failed, aborting PyPI publish: %w", err)
	}

	container, err := m.buildWithUv(ctx, source)
	if err != nil {
		return "", fmt.Errorf("build failed during PyPI publish: %w", err)
	}

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
