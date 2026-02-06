package main

import (
	"context"
	"dagger/ra-mcp/internal/dagger"
	"fmt"
)

// ScanSeverity represents Trivy scan severity levels
type ScanSeverity string

const (
	SeverityCritical ScanSeverity = "CRITICAL"
	SeverityHigh     ScanSeverity = "HIGH"
	SeverityMedium   ScanSeverity = "MEDIUM"
	SeverityLow      ScanSeverity = "LOW"
	SeverityUnknown  ScanSeverity = "UNKNOWN"
)

// Scan performs container vulnerability scanning using Trivy
func (m *RaMcp) Scan(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Severity levels to report (comma-separated: CRITICAL,HIGH,MEDIUM,LOW,UNKNOWN)
	// +default="CRITICAL,HIGH"
	severity string,
	// Output format (table, json, sarif, cyclonedx, spdx, github)
	// +default="table"
	format string,
	// Exit code when vulnerabilities are found (0 to ignore vulnerabilities)
	// +default=1
	exitCode int,
) (string, error) {
	// Build the container first
	container, err := m.Build(ctx, source, "")
	if err != nil {
		return "", fmt.Errorf("build failed before scanning: %w", err)
	}

	// Export container to tar for scanning
	tarFile := container.AsTarball()

	// Create Trivy scanner container
	trivyContainer := dag.Container().
		From("aquasec/trivy:latest").
		WithMountedFile("/image.tar", tarFile).
		WithExec([]string{
			"trivy",
			"image",
			"--input", "/image.tar",
			"--severity", severity,
			"--format", format,
			"--exit-code", fmt.Sprintf("%d", exitCode),
		})

	// Get scan results
	output, err := trivyContainer.Stdout(ctx)
	if err != nil {
		// Trivy returns error if vulnerabilities found with exit-code > 0
		// Try to get stdout anyway to show results
		if output == "" {
			return "", fmt.Errorf("trivy scan failed: %w", err)
		}
		return output, fmt.Errorf("vulnerabilities found: %w", err)
	}

	return output, nil
}

// ScanJson performs vulnerability scanning and returns JSON output
func (m *RaMcp) ScanJson(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Severity levels to report
	// +default="CRITICAL,HIGH"
	severity string,
) (string, error) {
	return m.Scan(ctx, source, severity, "json", 0)
}

// ScanCi performs vulnerability scanning for CI/CD pipeline
// Fails build if CRITICAL or HIGH vulnerabilities are found
func (m *RaMcp) ScanCi(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
) (string, error) {
	output, err := m.Scan(ctx, source, "CRITICAL,HIGH", "table", 1)
	if err != nil {
		return output, fmt.Errorf("CI scan failed - critical/high vulnerabilities found: %w", err)
	}
	return output, nil
}

// ScanSarif generates SARIF output for GitHub Security tab integration
func (m *RaMcp) ScanSarif(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Output file path for SARIF results
	// +default="trivy-results.sarif"
	outputPath string,
) (*dagger.File, error) {
	container, err := m.Build(ctx, source, "")
	if err != nil {
		return nil, fmt.Errorf("build failed before scanning: %w", err)
	}

	tarFile := container.AsTarball()

	trivyContainer := dag.Container().
		From("aquasec/trivy:latest").
		WithMountedFile("/image.tar", tarFile).
		WithExec([]string{
			"trivy",
			"image",
			"--input", "/image.tar",
			"--format", "sarif",
			"--output", "/output/" + outputPath,
		}).
		WithExec([]string{"cat", "/output/" + outputPath})

	return trivyContainer.File("/output/" + outputPath), nil
}

// GenerateSbom generates Software Bill of Materials (SBOM) for the container
func (m *RaMcp) GenerateSbom(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
	// SBOM format (spdx-json, cyclonedx, spdx, github)
	// +default="spdx-json"
	format string,
) (*dagger.File, error) {
	if baseImage == "" {
		baseImage = "python:3.12-alpine"
	}

	container, err := m.Build(ctx, source, baseImage)
	if err != nil {
		return nil, fmt.Errorf("build failed before SBOM generation: %w", err)
	}

	tarFile := container.AsTarball()

	trivyContainer := dag.Container().
		From("aquasec/trivy:latest").
		WithMountedFile("/image.tar", tarFile).
		WithExec([]string{"mkdir", "-p", "/output"}).
		WithExec([]string{
			"trivy",
			"image",
			"--input", "/image.tar",
			"--format", format,
			"--output", "/output/sbom.json",
		})

	return trivyContainer.File("/output/sbom.json"), nil
}

// GenerateSbomSpdx generates SPDX-format SBOM
func (m *RaMcp) GenerateSbomSpdx(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
) (*dagger.File, error) {
	return m.GenerateSbom(ctx, source, baseImage, "spdx-json")
}

// GenerateSbomCycloneDx generates CycloneDX-format SBOM
func (m *RaMcp) GenerateSbomCycloneDx(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
) (*dagger.File, error) {
	return m.GenerateSbom(ctx, source, baseImage, "cyclonedx")
}

// ExportSbom generates and exports SBOM to a local file
func (m *RaMcp) ExportSbom(
	ctx context.Context,
	// Source directory containing Dockerfile and application code
	// +defaultPath="/"
	// +optional
	source *dagger.Directory,
	// Base image to use for the build
	// +default="python:3.12-alpine"
	// +optional
	baseImage string,
	// SBOM format (spdx-json, cyclonedx, spdx, github)
	// +default="spdx-json"
	format string,
	// Output file path
	// +default="./sbom.json"
	outputPath string,
) (string, error) {
	sbomFile, err := m.GenerateSbom(ctx, source, baseImage, format)
	if err != nil {
		return "", err
	}

	// Export the file
	_, err = sbomFile.Export(ctx, outputPath)
	if err != nil {
		return "", fmt.Errorf("failed to export SBOM: %w", err)
	}

	return fmt.Sprintf("SBOM exported to %s", outputPath), nil
}

// VerifyAttestations verifies SBOM and provenance attestations for a published image
// Uses cosign to inspect attestations embedded in the OCI registry
func (m *RaMcp) VerifyAttestations(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
) (string, error) {
	// Use cosign container to verify attestations
	cosignContainer := dag.Container().
		From("gcr.io/projectsigstore/cosign:latest").
		WithExec([]string{
			"cosign",
			"verify-attestation",
			"--type", "slsaprovenance",
			"--insecure-ignore-tlog",
			"--insecure-ignore-sct",
			imageRef,
		})

	output, err := cosignContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("attestation verification failed: %w", err)
	}

	return output, nil
}

// InspectAttestations inspects all attestations attached to an image
// Shows SBOM, provenance, and other attestations without verification
func (m *RaMcp) InspectAttestations(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine or docker.io/riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
) (string, error) {
	// Add docker.io prefix if not present and no registry specified
	fullRef := imageRef
	if len(imageRef) > 0 && imageRef[0] != '/' && !containsRegistry(imageRef) {
		fullRef = "docker.io/" + imageRef
	}

	// Use oras to discover attestations
	orasContainer := dag.Container().
		From("ghcr.io/oras-project/oras:v1.2.2").
		WithExec([]string{
			"oras",
			"discover",
			"--format", "tree",
			fullRef,
		})

	output, err := orasContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to discover attestations: %w", err)
	}

	return output, nil
}

// Helper function to check if image ref contains a registry
func containsRegistry(imageRef string) bool {
	// Check for common patterns: contains "." or ":" before first "/"
	for _, c := range imageRef {
		if c == '/' {
			return false
		}
		if c == '.' || c == ':' {
			return true
		}
	}
	return false
}

// InspectImageManifest inspects the OCI manifest to show all layers including attestations
func (m *RaMcp) InspectImageManifest(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
) (string, error) {
	// Use crane to inspect the manifest
	craneContainer := dag.Container().
		From("gcr.io/go-containerregistry/crane:latest").
		WithExec([]string{
			"crane",
			"manifest",
			imageRef,
		})

	output, err := craneContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to inspect manifest: %w", err)
	}

	return output, nil
}

// DownloadSbom downloads the SBOM attestation from a published image
func (m *RaMcp) DownloadSbom(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
	// Output file path
	// +default="./downloaded-sbom.json"
	outputPath string,
) (string, error) {
	// Use cosign to download SBOM attestation
	cosignContainer := dag.Container().
		From("gcr.io/projectsigstore/cosign:latest").
		WithExec([]string{
			"cosign",
			"download",
			"attestation",
			"--predicate-type", "https://spdx.dev/Document",
			imageRef,
		})

	sbomContent, err := cosignContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to download SBOM: %w", err)
	}

	// Write to file
	sbomFile := dag.Container().
		From("alpine:latest").
		WithNewFile("/sbom.json", sbomContent).
		File("/sbom.json")

	_, err = sbomFile.Export(ctx, outputPath)
	if err != nil {
		return "", fmt.Errorf("failed to export SBOM: %w", err)
	}

	return fmt.Sprintf("SBOM downloaded to %s", outputPath), nil
}

// CheckAttestationCount checks how many attestations are attached to an image
// Useful for quick verification that SBOM and provenance were published
func (m *RaMcp) CheckAttestationCount(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
) (string, error) {
	// Use Docker Hub API or crane to check manifest list
	craneContainer := dag.Container().
		From("gcr.io/go-containerregistry/crane:latest").
		WithExec([]string{
			"sh", "-c",
			fmt.Sprintf("crane manifest %s | grep -o '\"mediaType\"' | wc -l", imageRef),
		})

	count, err := craneContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to count attestations: %w", err)
	}

	return fmt.Sprintf("Image %s has attestations (manifest entries: %s)", imageRef, count), nil
}

// ShowAttestationContents shows the raw contents of attestations attached to an image
// This displays the actual SBOM and provenance data from BuildKit attestations
func (m *RaMcp) ShowAttestationContents(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
	// Which platform's attestation to show (amd64 or arm64)
	// +default="amd64"
	platform string,
) (string, error) {
	// Add docker.io prefix if needed
	fullRef := imageRef
	if len(imageRef) > 0 && imageRef[0] != '/' && !containsRegistry(imageRef) {
		fullRef = "docker.io/" + imageRef
	}

	// Use crane and jq to extract attestation manifests
	// BuildKit stores attestations as separate manifests with annotation "vnd.docker.reference.type": "attestation-manifest"
	// Get crane binary from official image
	craneBinary := dag.Container().
		From("gcr.io/go-containerregistry/crane:latest").
		File("/ko-app/crane")

	// Use alpine with jq and copy crane binary
	craneContainer := dag.Container().
		From("alpine:latest").
		WithExec([]string{"apk", "add", "--no-cache", "jq"}).
		WithFile("/usr/local/bin/crane", craneBinary).
		WithExec([]string{
			"sh", "-c",
			fmt.Sprintf(`
# Get the main manifest list
MANIFEST=$(crane manifest %s)

# Find attestation manifest digests for the specified platform
# First get the platform image digest
PLATFORM_DIGEST=$(echo "$MANIFEST" | jq -r '.manifests[] | select(.platform.architecture == "%s" and .platform.os == "linux") | .digest')

# Then find the attestation manifest that references this platform
ATTESTATION_DIGEST=$(echo "$MANIFEST" | jq -r --arg ref "$PLATFORM_DIGEST" '.manifests[] | select(.annotations."vnd.docker.reference.type" == "attestation-manifest" and .annotations."vnd.docker.reference.digest" == $ref) | .digest')

if [ -z "$ATTESTATION_DIGEST" ]; then
  echo "No attestation found for platform %s"
  exit 0
fi

echo "=== Attestation Manifest for %s ==="
echo "Digest: $ATTESTATION_DIGEST"
echo ""

# Get the attestation manifest
ATTESTATION_MANIFEST=$(crane manifest %s@$ATTESTATION_DIGEST)
echo "$ATTESTATION_MANIFEST" | jq .

# Get the actual attestation layers
echo ""
echo "=== Attestation Layers ==="
LAYERS=$(echo "$ATTESTATION_MANIFEST" | jq -r '.layers[] | .digest')
for LAYER in $LAYERS; do
  echo ""
  echo "--- Layer: $LAYER ---"
  crane blob %s@$LAYER | head -c 10000
  echo ""
done
			`, fullRef, platform, platform, platform, fullRef, fullRef),
		})

	output, err := craneContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to extract attestations: %w", err)
	}

	return output, nil
}

// ListAttestationTypes lists what types of attestations are attached to an image
func (m *RaMcp) ListAttestationTypes(
	ctx context.Context,
	// Container image reference (e.g., riksarkivet/ra-mcp:v0.2.8-alpine)
	imageRef string,
) (string, error) {
	// Add docker.io prefix if needed
	fullRef := imageRef
	if len(imageRef) > 0 && imageRef[0] != '/' && !containsRegistry(imageRef) {
		fullRef = "docker.io/" + imageRef
	}

	// Use crane to inspect each attestation manifest
	craneContainer := dag.Container().
		From("gcr.io/go-containerregistry/crane:latest").
		WithExec([]string{
			"sh", "-c",
			fmt.Sprintf(`crane manifest %s | jq -r '.manifests[] | select(.annotations."vnd.docker.reference.type" == "attestation-manifest") | "Attestation for: " + .annotations."vnd.docker.reference.digest" + "\nDigest: " + .digest'`, fullRef),
		})

	output, err := craneContainer.Stdout(ctx)
	if err != nil {
		return "", fmt.Errorf("failed to list attestations: %w", err)
	}

	return output, nil
}
