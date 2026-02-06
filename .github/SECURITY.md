# Security Policy

## Reporting Security Vulnerabilities

**Please do not report security vulnerabilities through public GitHub issues.**

Report them via:
- **GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/AI-Riksarkivet/ra-mcp/security/advisories/new)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

## Software Bill of Materials (SBOM)

SBOMs are provided for all releases to enable supply chain transparency.

### Accessing SBOMs

**From GitHub Releases:**
```bash
wget https://github.com/AI-Riksarkivet/ra-mcp/releases/download/v0.2.8/sbom.spdx.json
```

**From Container Registry:**
```bash
# Inspect SBOM attestation
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.2.8 --format "{{json .SBOM}}"
```

**Generate Locally:**
```bash
dagger call export-sbom --format spdx-json --output-path ./sbom.spdx.json
```

### SBOM Format

- **SPDX 2.3** - ISO/IEC 5962:2021 international standard

## Security Features

- ✅ SBOM generation (SPDX 2.3 format)
- ✅ SLSA provenance attestations (Level 2)
- ✅ Cosign image signing (keyless with Sigstore)
- ✅ OpenSSF Scorecard monitoring
- ✅ Alpine-based minimal images
- ✅ Multi-platform support (amd64, arm64)
- ✅ Automated vulnerability scanning

## SLSA Build Level 2

This project achieves [SLSA Build Level 2](https://slsa.dev/spec/v1.0/levels#build-l2) through:
- ✅ **Provenance generated**: BuildKit generates signed provenance attestations
- ✅ **Authenticated provenance**: GitHub OIDC provides cryptographic identity
- ✅ **Service-generated**: Built on GitHub-hosted runners
- ✅ **Non-falsifiable**: Provenance signed and verifiable

**Note**: Level 3 requires isolated, ephemeral build environments which standard GitHub Actions runners don't provide. To achieve Level 3, we would need to use `slsa-framework/slsa-github-generator` with dedicated hardened runners.

## Image Signing and Verification

All images are signed with Cosign using keyless signing (Sigstore).

### Verify Image Signature

```bash
# Verify signature (requires Cosign)
cosign verify riksarkivet/ra-mcp:v0.2.9 \
  --certificate-identity-regexp "^https://github.com/AI-Riksarkivet/ra-mcp/" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com

# Verify attestations
cosign verify-attestation riksarkivet/ra-mcp:v0.2.9 \
  --type slsaprovenance \
  --certificate-identity-regexp "^https://github.com/AI-Riksarkivet/ra-mcp/" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

## Vulnerability Scanning

Scan published images:
```bash
# Using Docker Scout
docker scout cves riksarkivet/ra-mcp:latest

# Using Trivy
trivy image riksarkivet/ra-mcp:latest
```

## References

- [SPDX Specification](https://spdx.dev/specifications/)
- [SLSA Framework](https://slsa.dev/)
- [Docker Build Attestations](https://docs.docker.com/build/metadata/attestations/)
