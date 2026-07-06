# HIPAA Compliance Considerations

This document outlines the security and compliance measures built into the platform for handling Protected Health Information (PHI).

## What is PHI in This System?

The following data elements are PHI and require protection:
- Patient names
- Dates of birth
- Phone numbers, email addresses
- Medical record numbers / Member IDs
- Prescription details (linked to a patient)
- Diagnosis codes
- Lab results
- Clinical notes
- Insurance information

## Security Controls

### 1. Encryption at Rest

**Implementation:** `backend/app/utils/encryption.py`

- All PHI fields are encrypted using AES-256 via the Fernet algorithm
- Encryption key is stored as an environment variable (never in code)
- Each field is encrypted individually before database storage
- Decryption happens only at the application layer, not in DB queries

**Production note:** Use AWS KMS or HashiCorp Vault for key management in production.

### 2. Encryption in Transit

- All API traffic should use HTTPS (TLS 1.3)
- Docker services communicate over an internal network
- External integrations (CoverMyMeds, fax APIs) use TLS

### 3. Audit Logging

**Implementation:** `backend/app/models/audit_log.py`, `backend/app/services/audit_service.py`

Every data access is logged with:
- Who accessed it (user_id)
- What they accessed (resource_type, resource_id)
- When (timestamp)
- From where (IP address, user agent)
- Whether PHI was accessed (phi_accessed flag)
- Before/after values for modifications

Audit logs are **immutable** — they can only be appended, never modified or deleted.

### 4. Authentication & Authorization

**Implementation:** `backend/app/security.py`

- JWT-based authentication
- Tokens expire after 60 minutes
- Role-based access control:
  - **admin**: Full access, user management
  - **pharmacist**: Full workflow access
  - **technician**: Limited to assigned tasks
  - **readonly**: Dashboard and reporting only

### 5. Minimum Necessary Access

Each AI agent only receives the data it needs:
- The `AgentContext` carries only IDs
- Agents load specific records from the database
- Agents don't have access to unrelated patient data

### 6. AI/LLM Considerations

**Critical for HIPAA compliance with AI:**

- **Business Associate Agreement (BAA):** Required with Anthropic if sending PHI to Claude
- **Data minimization:** Only send the minimum necessary PHI in prompts
- **No training on PHI:** Confirm with Anthropic that data is not used for training
- **Audit trail for AI:** Every Claude API call is logged (tokens, content summary)

**Production recommendation:** Consider using a self-hosted LLM or Anthropic's API with a signed BAA for actual PHI processing.

### 7. Data Retention

- Active PA data: Retained for the life of the case + 7 years
- Audit logs: Retained for 6 years (HIPAA requirement)
- Communication logs: Retained for 6 years
- AI execution logs: Retained for 3 years

**Implementation:** A Celery task archives old records to cold storage.

## HIPAA Administrative Requirements

### Policies Needed for Production

1. **Privacy Policy** — How PHI is collected, used, and disclosed
2. **Security Policy** — Technical and administrative safeguards
3. **Breach Notification Policy** — How to respond to data breaches
4. **Business Associate Agreements** — With Anthropic, cloud providers, fax services
5. **Access Control Policy** — Who can access what, and how access is granted/revoked
6. **Training Program** — Staff training on HIPAA requirements

### Risk Assessment Items

| Risk | Mitigation |
|------|-----------|
| PHI sent to LLM provider | BAA with Anthropic; minimize data sent |
| Database breach | Encryption at rest + field-level encryption |
| Unauthorized access | JWT auth + RBAC + audit logging |
| Staff device loss | No PHI stored on client devices; server-side only |
| Fax misdirection | Confirm fax numbers before sending |
| Webhook data exposure | HTTPS + signature verification on inbound webhooks |
| Log exposure | PHI not included in application logs; audit log separate |

## Implementation Checklist

- [x] Field-level encryption for PHI (AES-256)
- [x] Audit logging for all data access
- [x] JWT authentication
- [x] Role-based access control (framework)
- [x] Agent execution logging
- [x] Structured logging without PHI
- [ ] HTTPS enforcement (configure in production)
- [ ] BAA with Anthropic
- [ ] BAA with cloud provider (AWS)
- [ ] Data retention automation
- [ ] Breach notification procedures
- [ ] Penetration testing
- [ ] Security awareness training

## Environment-Specific Notes

### Development (Current)
- Running on localhost without HTTPS (acceptable for dev)
- Using plain-text secrets in `.env` file
- No BAA required for synthetic/test data

### Production Requirements
- HTTPS mandatory with valid TLS certificate
- Secrets in AWS Secrets Manager or HashiCorp Vault
- BAA with all vendors handling PHI
- Network segmentation (VPC, security groups)
- Regular vulnerability scanning
- SOC 2 compliance recommended for enterprise customers
- Annual HIPAA risk assessment

## Relevant HIPAA Rules

- **Privacy Rule (45 CFR Part 160, 164 Subparts A, E):** Governs use and disclosure of PHI
- **Security Rule (45 CFR Part 160, 164 Subparts A, C):** Technical safeguards for ePHI
- **Breach Notification Rule (45 CFR Part 164 Subpart D):** Required notifications after breach
- **HITECH Act:** Increased penalties, extends requirements to business associates
