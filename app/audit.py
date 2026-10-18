"""Rule-based audit over the local register, preserving evidence provenance."""
import json
from uuid import uuid4
from .store import connect, now, record_event

def classify_account(account):
    """Return rule findings for one account-shaped dict; reusable by fixtures."""
    roles=account.get("people_roles", [])
    checks=[
      (bool(account.get("recovery_email")) and not account["recovery_email"].endswith("@company.example.invalid"), "non_company_recovery", "high", "Recovery email is outside the company test domain."),
      (not account.get("backup_codes_in_vault"), "missing_backup_codes", "high", "Backup codes are not recorded as stored in the approved vault."),
      (not account.get("two_factor_enabled"), "incomplete_security", "critical", "Two-factor authentication is not marked complete."),
      (any(p.get("role") in ("Admin","Owner") and p.get("last_verified","9999") < "2026-01-01" for p in roles), "stale_access", "medium", "Privileged access record is stale and needs human review.")]
    label=account.get("evidence_label","unverified")
    if label not in ("integration-verified","human-confirmed","unverified"): label="unverified"
    return [{"type":kind,"severity":severity,"label":label,"evidence":evidence,"remediation_status":"open"}
            for condition,kind,severity,evidence in checks if condition]

def run_audit(correlation_id=None):
    made=[]
    with connect() as db:
        db.execute("DELETE FROM findings")
        accounts=db.execute("SELECT * FROM accounts").fetchall()
        for account in accounts:
            label=account["evidence_label"] if account["evidence_label"] in ("integration-verified","human-confirmed","unverified") else "unverified"
            source=dict(account)
            source["people_roles"]=json.loads(account["people_roles"])
            for finding in classify_account(source):
                fid=str(uuid4())
                db.execute("INSERT INTO findings VALUES(?,?,?,?,?,?,?,?)", (fid,account["id"],finding["type"],finding["severity"],finding["label"],finding["evidence"],finding["remediation_status"],now()))
                task_key=f"audit-remediation:{account['id']}:{finding['type']}"
                task=db.execute("SELECT id FROM tasks WHERE idempotency_key=?",(task_key,)).fetchone()
                if not task:
                    task_id=str(uuid4()); timestamp=now()
                    db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)",(task_id,task_key,account["id"],f"Remediate {finding['type']}",account["owner"],None,"open",finding["evidence"],None,timestamp,timestamp))
                else:
                    task_id=task["id"]
                made.append({"id":fid,"account_id":account["id"],"follow_up_task_id":task_id,**finding})
    record_event("audit_completed", {"finding_count":len(made)}, correlation_id)
    return {"finding_count":len(made),"findings":made,"data_scope":"local prototype records only"}
