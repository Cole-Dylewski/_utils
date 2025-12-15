# Security Policy

## Supported Versions

Currently supported versions of `_utils` receive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in `_utils`, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [Your Email] or create a private security advisory on GitHub
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within 48 hours and provide an update on the timeline for addressing the issue.

## Security Best Practices

When using `_utils` in your applications:

### Credential Management
- ✅ Use environment variables for API keys, tokens, and secrets
- ✅ Never commit credentials to version control
- ✅ Use AWS Secrets Manager or HashiCorp Vault for production
- ✅ Rotate credentials regularly

### Data Handling
- ✅ Never log sensitive data (passwords, tokens, keys, PII)
- ✅ Validate and sanitize all inputs
- ✅ Use parameterized queries for database operations
- ✅ Encrypt sensitive data at rest and in transit

### Network Security
- ✅ Always use HTTPS for API requests
- ✅ Verify SSL certificates
- ✅ Use connection timeouts
- ✅ Implement rate limiting for external APIs

### Code Security
- ✅ Keep dependencies up to date (`pip install --upgrade`)
- ✅ Review dependency security advisories
- ✅ Use the latest Python version (3.10+)
- ✅ Enable security scanning in CI/CD

### AWS Security
- ✅ Use IAM roles with least privilege
- ✅ Enable CloudTrail for audit logging
- ✅ Use VPC endpoints for private access
- ✅ Encrypt S3 buckets and DynamoDB tables

## Known Security Considerations

### Library-Specific Notes

1. **AWS Credentials**: The library uses boto3 which follows AWS credential chain. Ensure proper IAM permissions.

2. **Database Connections**: Always use connection pooling and parameterized queries to prevent SQL injection.

3. **API Keys**: Store Alpaca and other API keys securely. The library does not store credentials.

4. **Logging**: The library avoids logging sensitive data. Review your application's logging configuration.

5. **Network Requests**: All HTTP requests should use HTTPS. The library does not enforce this - ensure your environment is configured correctly.

## Dependency Security

We regularly update dependencies to address security vulnerabilities. To check for known vulnerabilities:

```bash
safety check
pip-audit
```

## Security Updates

Security updates will be:
- Released as patch versions (e.g., 0.1.0 → 0.1.1)
- Documented in CHANGELOG.md under "Security" section
- Tagged with security advisory on GitHub (if applicable)

## Thank You

Thank you for helping keep `_utils` and its users safe!
