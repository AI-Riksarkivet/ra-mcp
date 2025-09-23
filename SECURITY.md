# Security Policy

## Reporting Security Vulnerabilities

To report security vulnerabilities, email: ai@riksarkivet.se

**Do not report security issues through public GitHub issues.**

Include in your report:
- Issue type and location in code
- Steps to reproduce
- Potential impact
- Proof-of-concept if available

## Response Timeline

- Acknowledgment: 2 business days
- Assessment: 5 business days
- Resolution: 30 days for critical issues

## Security Measures

- Input validation with Pydantic models
- No sensitive data in error messages
- HTTPS/TLS for network communications
- Non-root Docker containers
- Minimal base images

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅        |
| < 1.0   | ❌        |