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
