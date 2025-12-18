---
status: active
created: 2025-12-18
updated: 2025-12-18
type: reference
lifecycle: persistent
---

# Security Policy

## Supported Versions

This is a Python package for automating Claude Code configuration. Security updates are applied via:
- Nix flake inputs (locked versions)
- Regular dependency updates

| Component | Version | Supported |
|-----------|---------|-----------|
| Python | 3.13 | Yes |
| Dependencies | See pyproject.toml | Yes |

## Reporting a Vulnerability

If you discover a security issue:

1. **Do not open a public issue** for security vulnerabilities
2. Email the maintainer directly or use GitHub's private vulnerability reporting
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix (if applicable)**: Depends on severity

## Security Considerations

### What This Tool Generates

- CLAUDE.md files (system context for Claude Code)
- Permission configurations (auto-approval patterns)
- Analytics reports (tool usage statistics)

### What This Tool Does NOT Handle

- Secrets, passwords, or API keys
- SSH keys or certificates
- Personal data or credentials
- Authentication tokens

### Security Best Practices

1. **Read-only analysis** - Only reads configuration files, doesn't modify system
2. **Local processing** - All analytics processed locally, no external transmission
3. **No credential storage** - Never stores or transmits credentials
4. **Transparent output** - All generated files are human-readable

## Dependency Security

Dependencies are managed through:
- `pyproject.toml` - Python dependencies
- `flake.lock` - Nix flake inputs

To update dependencies:
```bash
nix flake update
```

## Contact

- GitHub Issues: For non-security bugs and feature requests
- Private: Use GitHub's security advisory feature for vulnerabilities
