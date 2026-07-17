# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Properties & Threat Model

AgentCI is a pre-production deployment governance tool. Its primary threat model focuses on **Behavioral Regression** and **Prompt Injection Vulnerabilities**.

### Threats Mitigated
1. **Silent Model Updates:** Catching behavioral drift caused by underlying foundation model changes.
2. **Prompt Injection Regressions:** Ensuring that an agent remains resilient to adversarial inputs across versions by running injection test suites on every commit.
3. **Deployment Tampering:** Ensuring that no agent can reach production without a cryptographically verifiable evaluation report in the S3 vault.

### Trust Boundaries
- **Agent Execution:** Untrusted. The agent being evaluated is run in an isolated sandbox to prevent it from affecting the evaluation pipeline.
- **Bedrock Judge:** Trusted. The LLM-as-a-Judge is assumed to act honestly based on the system prompt, though score thresholds should be tuned to account for minor non-determinism.
- **Report Vault:** Trusted. S3 bucket policies must enforce WORM (Write Once, Read Many) to prevent tampering with historical evaluation reports.

## Reporting a Vulnerability

If you discover a vulnerability in the evaluation logic, Step Functions state machine, or report generation, please report it securely.

**Do not open a public GitHub issue.**

Please email `ojack@merkabacreatives.org` with the subject `[Security] AgentCI Vulnerability`. Include steps to reproduce and potential impact. You will receive a response within 48 hours.
