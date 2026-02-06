# Container Attestations and SLSA

This document explains the attestations and supply chain security for the ra-mcp container images.

## Overview

ra-mcp publishes container images with multiple types of attestations:

1. **Standard images** (`riksarkivet/ra-mcp:*-alpine`) - SLSA Level 2-3 with BuildKit attestations
2. **SLSA L3 images** (`riksarkivet/ra-mcp:*-alpine-slsa`) - Full SLSA Level 3 with signed provenance

## Attestation Types

### 1. SBOM (Software Bill of Materials)

- **Format**: SPDX 2.3 JSON
- **Generator**: Syft (via BuildKit)
- **Content**: Complete list of all packages, dependencies, and licenses

### 2. SLSA Provenance

- **Standard images**: SLSA v0.2 (BuildKit)
- **SLSA L3 images**: SLSA v1.0 (slsa-github-generator)
- **Content**: Builder identity, build materials, parameters, and full GitHub Actions context

## Verifying Attestations

### Using Dagger (No Docker Required)

Check the SLSA level of any image:

```bash
dagger call check-slsa-level --image-ref riksarkivet/ra-mcp:v0.2.8-alpine-slsa
```

View attestation contents:

```bash
dagger call show-attestation-contents --image-ref riksarkivet/ra-mcp:v0.2.8-alpine-slsa
```

Inspect the OCI manifest:

```bash
dagger call inspect-image-manifest --image-ref riksarkivet/ra-mcp:v0.2.8-alpine-slsa
```

### Using Cosign (SLSA L3 images only)

Verify signed provenance:

```bash
# Install cosign
brew install cosign  # macOS
# or download from https://github.com/sigstore/cosign/releases

# Verify provenance (no key needed - uses keyless signing)
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp "^https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_container_slsa3.yml@refs/tags/v[0-9]+.[0-9]+.[0-9]+$" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  riksarkivet/ra-mcp:v0.2.8-alpine-slsa
```

Download and view provenance:

```bash
cosign download attestation riksarkivet/ra-mcp:v0.2.8-alpine-slsa | jq .
```

### Using Docker Buildx

Inspect attestations (Docker 20.10+):

```bash
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.2.8-alpine-slsa --format "{{ json .Provenance }}"
```

### Using ORAS

Discover attestations:

```bash
# Install ORAS
brew install oras  # macOS

# Discover attestations
oras discover riksarkivet/ra-mcp:v0.2.8-alpine-slsa
```

### Using Crane

View the full OCI manifest:

```bash
# Install crane
go install github.com/google/go-containerregistry/cmd/crane@latest

# View manifest with attestations
crane manifest riksarkivet/ra-mcp:v0.2.8-alpine-slsa | jq .
```

## SLSA Build Levels

### Standard Images (BuildKit)

**SLSA Level: 2-3** (with SLSA v0.2 format)

✅ **Level 1**: Build process exists
- Provenance is generated and embedded

✅ **Level 2**: Documented build process
- Builder identified (GitHub Actions)
- Automated provenance generation

✅ **Level 3 Indicators**:
- Build on hosted platform (GitHub Actions)
- Tamper-resistant (embedded in OCI registry)
- Note: Uses SLSA v0.2 format (not v1.0)

### SLSA L3 Images (slsa-github-generator)

**SLSA Level: 3** (with SLSA v1.0 format)

✅ **Level 1**: Build process exists
✅ **Level 2**: Documented build process
✅ **Level 3**: Fully compliant
- SLSA v1.0 provenance format
- Signed with Sigstore (keyless signing)
- Non-falsifiable provenance
- Isolated build environment
- Parameterized builds
- Hermetic builds

## Provenance Contents

The provenance attestation includes:

- **Builder ID**: GitHub Actions workflow URL
- **Build Type**: Dockerfile-based build
- **Materials**: All base images with SHA256 digests
  - Base Python image
  - UV package manager image
  - BuildKit scanner image
- **Build Parameters**:
  - Dockerfile location
  - Build arguments
  - Build context
- **GitHub Context**:
  - Repository information
  - Release details
  - Actor who triggered the build
  - Complete event payload

## Security Properties

### Tamper Resistance

Attestations are embedded in the OCI registry as content-addressable layers:
- Each attestation has a unique SHA256 digest
- Modifying attestations would change the digest
- Registries provide integrity guarantees

### Traceability

Each build links back to:
- Specific GitHub Actions workflow run
- Exact commit SHA
- Release tag
- User who triggered the build

### Reproducibility

The provenance includes:
- All source materials with digests
- Complete build parameters
- Build environment details

This allows verification that the image was built from the expected sources.

## Best Practices

### For Consumers

1. **Verify provenance before using images**:
   ```bash
   dagger call check-slsa-level --image-ref riksarkivet/ra-mcp:latest-alpine-slsa
   ```

2. **Check builder identity**:
   - Ensure it points to the official repository
   - Verify the GitHub Actions run URL

3. **Inspect SBOM for vulnerabilities**:
   ```bash
   dagger call show-attestation-contents --image-ref riksarkivet/ra-mcp:latest-alpine-slsa --platform amd64
   ```

4. **Use SLSA L3 images for production** when maximum security is required

### For Maintainers

1. **Always publish attestations** with container images
2. **Use SLSA L3 workflow** for releases
3. **Keep base images updated** to minimize vulnerabilities
4. **Review provenance contents** before publishing

## Compliance

These attestations support compliance with:

- **SLSA Framework**: Build Level 3
- **SSDF (Secure Software Development Framework)**: Supply chain security practices
- **NIST SP 800-218**: Secure software development
- **Executive Order 14028**: Supply chain security requirements

## Resources

- [SLSA Framework](https://slsa.dev/)
- [in-toto Attestation Format](https://in-toto.io/)
- [SPDX Specification](https://spdx.dev/)
- [Sigstore Cosign](https://docs.sigstore.dev/cosign/overview/)
- [slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator)
- [OCI Image Format](https://github.com/opencontainers/image-spec)
