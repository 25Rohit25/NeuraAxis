# Incident Response Playbook (PHI Data Breach)

**Severity**: CRITICAL
**Trigger**: Detection of unauthorized access to Patient Health Information (PHI).

## Phase 1: Detection & Identification

1. **Identify the Source**: Review `audit.log` (Splunk/ELK) for "ACCESS_DENIED" spikes or unusual "EXPORT" actions.
2. **Verify Breach**: Confirm if data was actually exfiltrated vs just a failed attempt.
3. **Declare Incident**: Trigger PagerDuty for "Security Incident Response Team".

## Phase 2: Containment

**Immediate Actions (Minimize Damage)**

1. **Revoke Access**:
   ```bash
   # Block user immediately
   python scripts/admin_cli.py block-user <USER_ID>
   ```
2. **Isolate Systems**: If an automated attack, block IP at WAF/Firewall level.
3. **Key Rotation**: If API keys compromised, rotate immediately using `scripts/rotate_keys.sh`.

## Phase 3: Eradication

1. **Patch Vulnerability**: If SQLi or XSS was used, hotfix the code and deploy immediately (`git cherry-pick`).
2. **Clean artifacts**: Remove any backdoors or unauthorized accounts created.
3. **Reset Credentials**: Force password reset for all affected users/admins.

## Phase 4: Recovery

1. **Validate Integrity**: Check database checksums or backups to ensure data integrity.
2. **Restore Service**: Bring systems back online in a controlled manner.
3. **Monitor**: Heightened monitoring for 48 hours.

## Phase 5: Notification (HIPAA Mandate)

**Timeline**: Must notify affected individuals and HHS within **60 days** of discovery (if > 500 records).

1. Isolate the list of affected Patient IDs.
2. Draft notification letter (Legal Team).
3. Notify HHS (OCR Portal).

## Phase 6: Post-Incident Review

1. Conduct "Blameless Post-Mortem".
2. Update this playbook.
3. Improve specific detection rules that failed.
