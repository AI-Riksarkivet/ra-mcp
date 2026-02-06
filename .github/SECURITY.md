# Security Policy

## Reporting Security Vulnerabilities

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:
- **GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/AI-Riksarkivet/ra-mcp/security/advisories/new)
- **Email**: [Add contact email if desired]

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide a more detailed response within 5 business days.

## Software Bill of Materials (SBOM)

We provide SBOM (Software Bill of Materials) for all published container images to enable supply chain transparency and vulnerability management.

### Accessing SBOMs

**Download from GitHub Releases:**
```bash
# SBOMs are attached to each release as assets
wget https://github.com/AI-Riksarkivet/ra-mcp/releases/download/v0.3.0/sbom-v0.3.0-alpine.spdx.json
wget https://github.com/AI-Riksarkivet/ra-mcp/releases/download/v0.3.0/sbom-v0.3.0-wolfi.spdx.json
```

**Registry Attestations** (if using attestation workflow):
```bash
# Inspect SBOM embedded in registry
docker buildx imagetools inspect riksarkivet/ra-mcp:v0.3.0-alpine --format "{{json .SBOM}}"

# Verify attestations
docker scout attestation riksarkivet/ra-mcp:v0.3.0-alpine
```

**Generate Locally:**
```bash
# See CLAUDE.md for detailed instructions on generating SBOMs locally
dagger call generate-sbom-spdx --source=. --base-image="python:3.12-alpine" export --path=./sbom.spdx.json
```

### SBOM Formats

- **SPDX 2.3** (default) - ISO/IEC 5962:2021 international standard
- **CycloneDX 1.6** - OWASP standard for security use cases

## Supported Standards

- SPDX 2.3 (ISO/IEC 5962:2021)
- CycloneDX 1.6
- NTIA Minimum Elements for SBOM
- Executive Order 14028 (Software Supply Chain Security)
- SLSA Build Level 3 (when using attestation workflow)

## Security Features

- ✅ Automated vulnerability scanning (Trivy)
- ✅ SBOM generation for all releases
- ✅ Multi-base-image security options (Alpine, Wolfi, Debian)
- ✅ Minimal CVE count with Chainguard images
- ✅ Regular security updates
- ✅ SLSA Provenance attestations (optional workflow)

## Base Image Security

We support multiple base images with different security profiles:

| Base Image | CVE Count | Best For |
|------------|-----------|----------|
| `python:3.12-alpine` | Low | General use, minimal size |
| `cgr.dev/chainguard/python:latest-dev` | Minimal | Security-critical deployments |
| `python:3.12-slim` | Medium | Maximum compatibility |

See [CLAUDE.md](../CLAUDE.md) for detailed security documentation and SBOM generation instructions.

## Security Updates

We monitor for security vulnerabilities and update dependencies regularly. To check for vulnerabilities in your deployment:

```bash
# Scan published image
docker scout cves riksarkivet/ra-mcp:v0.3.0-alpine

# Or use Trivy
trivy image riksarkivet/ra-mcp:v0.3.0-alpine
```

## References

- [SPDX Specification](https://spdx.dev/specifications/)
- [CycloneDX Specification](https://cyclonedx.org/specification/overview/)
- [SLSA Framework](https://slsa.dev/)
- [NTIA SBOM Minimum Elements](https://www.ntia.gov/files/ntia/publications/sbom_minimum_elements_report.pdf)
- [Docker Build Attestations](https://docs.docker.com/build/metadata/attestations/)
