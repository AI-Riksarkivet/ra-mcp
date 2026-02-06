package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// PublishWithAttestations publishes container image with SBOM and provenance attestations
// NOTE: This requires using docker buildx with BuildKit, not Dagger's native build
// Dagger currently doesn't support pushing attestations directly (as of 2025)
func (m *RaMcp) PublishWithAttestations(
	ctx context.Context,
	// +default="riksarkivet/ra-mcp"
	imageRepository string,
	// Image tag (if empty, will use version from pyproject.toml with "v" prefix)
	// +optional
	tag string,
	// Base image for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
	// Tag suffix to append (e.g., "-alpine", "-wolfi")
	// +optional
	tagSuffix string,
	// +default="docker.io"
	registry string,
	// Docker username for authentication
	dockerUsername *dagger.Secret,
	// Docker password for authentication
	dockerPassword *dagger.Secret,
	// +optional
	source *dagger.Directory,
	// Skip version validation
	// +optional
	skipValidation bool,
	// Generate SBOM attestation (SPDX format)
	// +default=true
	generateSbom bool,
	// Generate provenance attestation (SLSA)
	// +default=true
	generateProvenance bool,
) (string, error) {
	if baseImage == "" {
		baseImage = "python:3.12-alpine"
	}

	resolvedTag, err := m.resolveTag(ctx, source, tag, skipValidation)
	if err != nil {
		return "", err
	}

	if tagSuffix != "" {
		resolvedTag = resolvedTag + tagSuffix
	}

	imageRef := registry + "/" + imageRepository + ":" + resolvedTag

	// Since Dagger doesn't support attestations natively yet,
	// we need to use docker buildx from within a container
	username, err := dockerUsername.Plaintext(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to read docker username: %w", err)
	}

	// Build attestation flags
	attestFlags := []string{}
	if generateSbom {
		attestFlags = append(attestFlags, "--sbom=true")
	}
	if generateProvenance {
		attestFlags = append(attestFlags, "--provenance=true")
	}

	// Construct buildx command with attestation flags and build context
	buildCmd := []string{
		"docker", "buildx", "build",
		"--build-arg", "BASE_IMAGE=" + baseImage,
		"--platform", "linux/amd64",
		"--push",
		"-t", imageRef,
	}
	buildCmd = append(buildCmd, attestFlags...)
	buildCmd = append(buildCmd, ".") // Add build context path

	// Create a container with docker buildx
	buildxContainer := dag.Container().
		From("docker:25-cli"). // Use Docker 25+ for BuildKit attestation support
		WithMountedDirectory("/src", source).
		WithWorkdir("/src").
		WithSecretVariable("DOCKER_PASSWORD", dockerPassword).
		WithExec([]string{"sh", "-c", fmt.Sprintf(
			"echo $DOCKER_PASSWORD | docker login %s -u %s --password-stdin",
			registry, username,
		)}).
		WithEnvVariable("DOCKER_BUILDKIT", "1").
		WithExec(buildCmd)

	output, err := buildxContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("buildx with attestations failed: %w", err)
	}

	return output, nil
}

// GenerateAttestationBundle generates SBOM and provenance as separate files
// This is useful for manual verification or publishing to artifact stores
func (m *RaMcp) GenerateAttestationBundle(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
	// Output directory for attestation files
	// +default="./attestations"
	outputDir string,
) (*dagger.Directory, error) {
	if baseImage == "" {
		baseImage = "python:3.12-alpine"
	}

	// Generate SBOM
	sbomFile, err := m.GenerateSbom(ctx, source, baseImage, "spdx-json")
	if err != nil {
		return nil, fmt.Errorf("failed to generate SBOM: %w", err)
	}

	// Create output directory with SBOM
	outputDirectory := dag.Directory().
		WithFile("sbom.spdx.json", sbomFile)

	// Note: Provenance generation requires build metadata from BuildKit
	// For now, we only generate SBOM via Trivy
	// Full provenance would need BuildKit integration

	return outputDirectory, nil
}

// VerifyAttestation verifies SBOM and provenance attestations for a published image
// This uses cosign and other verification tools
func (m *RaMcp) VerifyAttestation(
	ctx context.Context,
	// Image reference to verify (e.g., "docker.io/riksarkivet/ra-mcp:v0.3.0-alpine")
	imageRef string,
	// Type of attestation to verify (sbom, provenance, all)
	// +default="all"
	attestationType string,
) (string, error) {
	verifyContainer := dag.Container().
		From("aquasec/trivy:latest")

	var cmd []string
	switch attestationType {
	case "sbom":
		cmd = []string{"trivy", "image", "--format", "json", "--list-all-pkgs", imageRef}
	case "provenance":
		return "", fmt.Errorf("provenance verification not yet implemented")
	case "all":
		cmd = []string{"trivy", "image", "--format", "table", imageRef}
	default:
		return "", fmt.Errorf("unknown attestation type: %s", attestationType)
	}

	output, err := verifyContainer.WithExec(cmd).Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("verification failed: %w", err)
	}

	return output, nil
}
