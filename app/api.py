Warning: truncated output (original token count: 5054)
Total output lines: 327

import logging
import re
import uuid
from datetime import datetime, timezone
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from .store import connect, seed_demo, now, record_event
from .audit import run_audit
from .provisioning import PROVISIONING_STEPS

logging.basicConfig(level=logging.INFO)
app=FastAPI(title="Brand Operations Prototype",version="0.1.0",description="Human-gated coordination demo; no Instagram automation.")

@app.on_event("startup")
def startup():
    seed_demo()

@app.middleware("http")
async def request_context(request:Request, call_next):
    cid=request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id=cid
    response=await call_next(request)
    response.headers["X-Correlation-ID"]=cid
    return response

@app.exception_handler(Exception)
async def safe_error(request, exc):
    cid=getattr(request.state,"correlation_id","unknown")
    logging.error("unhandled_error correlation_id=%s exception_type=%s",cid,type(exc).__name__)
    return JSONResponse(status_code=500,content={"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred.","correlation_id":cid}})

class TaskIn(BaseModel):
    idempotency_key:str=Field(min_length=3,max_length=120)
    account_id:str
    title:str=Field(min_length=3,max_length=160)
    owner:str=Field(min_length=2,max_length=100)
    due_at:str|None=None
    instructions:str=Field(min_length=3,max_length=2000)

class TaskUpdate(BaseModel):
    status:str
    evidence:str|None=Field(default=None,max_length=1000)
    @field_validator("status")
    @classmethod
    def valid_status(cls,v):
        if v not in {"open","in_progress","completed","blocked"}:
            raise ValueError("unsupported status")
        return v
    @model_validator(mode="after")
    def completed_requires_evidence(self):
        if self.status=="completed" and not (self.evidence or "").strip():
            raise ValueError("redacted completion evidence is required")
        return self

class AccountCreate(BaseModel):
    brand:str=Field(min_length=2,max_length=100)
    handle:str=Field(min_length=1,max_length=30)
    owner:str=Field(min_length=2,max_length=100)
    recovery_email:str|None=Field(default=None,max_length=254)
    recovery_phone:str|None=Field(default=None,max_length=40)
    @field_validator("handle")
    @classmethod
    def valid_handle(cls,v):
        if not re.fullmatch(r"[A-Za-z0-9._]{1,30}",v):
            raise ValueError("handle must contain only letters, numbers, periods, or underscores")
        return v
    @field_validator("recovery_email")
    @classmethod
    def valid_email(cls,v):
        if v and ("@" not in v or v.startswith("@") or v.endswith("@")):
            raise ValueError("recovery email must be a valid email address")
        return v

class ProvisioningWorkflowIn(BaseModel):
    owner:str=Field(min_length=2,max_length=100)
    due_at:str=Field(min_length=10,max_length=40)
    @field_validator("due_at")
    @classmethod
    def valid_deadline(cls,v):
        try: parsed=datetime.fromisoformat(v.replace("Z","+00:00"))
        except ValueError: raise ValueError("due_at must be an ISO-8601 date/time")
        if parsed.tzinfo is None: raise ValueError("due_at must include a timezone offset")
        return v

class OffboardingIn(BaseModel):
    departing_person:str=Field(min_length=2,max_length=100)
    owner:str=Field(min_length=2,max_length=100)
    due_at:str=Field(min_length=10,max_length=40)
    @field_validator("due_at")
    @classmethod
    def valid_deadline(cls,v):
        try: parsed=datetime.fromisoformat(v.replace("Z","+00:00"))
        except ValueError: raise ValueError("due_at must be an ISO-8601 date/time")
        if parsed.tzinfo is None: raise ValueError("due_at must include a timezone offset")
        return v

class ProxySimulationIn(BaseModel):
    primary_failures:int=Field(default=3,ge=0,le=5)
    secondary_healthy:bool=True
    security_challenge:bool=False

class ProfileUpdate(BaseModel):
    profile_name:str=Field(min_length=1,max_length=100)
    bio:str=Field(max_length=150)
    profile_link:str=Field(max_length=500)
    category:str=Field(min_length=1,max_length=100)
    image_ref:str=Field(min_length=1,max_length=300)
    evidence_note:str=Field(min_length=3,max_length=500)

@app.get("/health")
def health():
    return {"status":"ok","mode":"demo"}

def mask_email(value):
    if not value:return None
    left,sep,domain=value.partition("@")
    return left[:1]+"***@"+domain if sep else "[redacted]"

def mask_phone(value):
    return "***"+value[-4:] if value else None

@app.get("/api/accounts")
def accounts():
    import json
    with connect() as db: rows=db.execute("SELECT * FROM accounts ORDER BY brand").fetchall()
    result=[]
    for row in rows:
        item=dict(row)
        item["recovery_email"]=mask_email(item["recovery_email"])
        item["recovery_phone"]=mask_phone(item["recovery_phone"])
        for key in ("vault_refs","people_roles","blockers"):
            item[key]=json.loads(item[key])
        result.append(item)
    return result

@app.post("/api/accounts",status_code=201)
def create_account(body:AccountCreate,request:Request):
    """Create an unverified register record only; no platform account is created."""
    account_id=str(uuid.uuid4()); timestamp=now()
    blockers='["Company authorization and test resources have not been verified"]'
    with connect() as db:
        try:
            db.execute("INSERT INTO accounts(id,brand,handle,owner,recovery_email,recovery_phone,status,blockers,evidence_label,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(account_id,body.brand,body.handle,body.owner,body.recovery_email,body.recovery_phone,"blocked",blockers,"unverified",timestamp))
        except Exception as exc:
            if "UNIQUE constraint failed: accounts.handle" in str(exc):
                raise HTTPException(409,detail={"code":"HANDLE_ALREADY_REGISTERED","message":"That handle already exists in this local register."})
            raise
    record_event("account_register_record_created",{"account_id":account_id,"brand":body.brand,"platform_account_created":False},request.state.correlation_id)
    return {"id":account_id,"brand":body.brand,"handle":body.handle,"owner":body.owner,"status":"blocked","blockers":["Company authorization and test resources have not been verified"],"evidence_label":"unverified","platform_account_created":False}

@app.get("/api/provisioning/steps")
def provisioning_steps():
    return {"steps":PROVISIONING_STEPS,"platform_actions":"human-only","company_access_available":False}

@app.post("/api/accounts/{account_id}/provisioning-workflow")
def create_provisioning_workflow(account_id:str,body:ProvisioningWorkflowIn,request:Request):
    """Create idempotent human tasks; does not create or modify a platform account."""
    created=[]
    with connect() as db:
        if not db.execute("SELECT 1 FROM accounts WHERE id=?",(account_id,)).fetchone():
            raise HTTPException(404,detail={"code":"ACCOUNT_NOT_FOUND","message":"Account register record not found."})
        for index,step in enumerate(PROVISIONING_STEPS,1):
            key=f"provisioning:{account_id}:{step['step_id']}"
            row=db.execute("SELECT * FROM tasks WHERE idempotency_key=?",(key,)).fetchone()
            deduplicated=bool(row)
            if not row:
                task_id=str(uuid.uuid4()); timestamp=now()
                gate="Complete only after the preceding step is complete. If authorization or an access dependency is absent, keep this task blocked and do not proceed. "
                title=f"[{index:02d}/{len(PROVISIONING_STEPS):02d}] {step['title']}"
                initial_status="open" if index==1 else "blocked"
                db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)",(task_id,key,account_id,title,body.owner,body.due_at,initial_status,gate+step["instructions"],None,timestamp,timestamp))
                row=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
            created.append({**dict(row),"deduplicated":deduplicated})
    record_event("human_provisioning_workflow_created",{"account_id":account_id,"step_count":len(created),"platform_actions_performed":False},request.state.correlation_id)
    return {"account_id":account_id,"task_count":len(created),"tasks":created,"platform_actions_performed":False,"environment_status":"company access not supplied; authorization gate must be cleared by human"}

@app.patch("/api/accounts/{account_id}/profile")
def update_profile(account_id:str,body:ProfileUpdate,request:Request):
    """Record supplied profile fields; does not edit Instagram or verify the operator."""
    with connect() as db:
        if not db.execute("SELECT 1 FROM accounts WHERE id=?",(account_id,)).fetchone():
            raise HTTPException(404,detail={"code":"ACCOUNT_NOT_FOUND","message":"Account record not found."})
        db.execute("UPDATE accounts SET profile_name=?,bio=?,profile_link=?,category=?,image_ref=?,evidence_label='unverified',updated_at=? WHERE id=?",(body.profile_name,body.bio,body.profile_link,body.category,body.image_ref,now(),account_id))
    record_event("profile_fields_recorded",{"account_id":account_id,"evidence_note":body.evidence_note,"platform_changed":False},request.state.correlation_id)
    return {"account_id":account_id,"recorded":True,"platform_changed":False,"evidence_label":"unverified","note":"The application has no authenticated operator identity to assert human confirmation."}

@app.get("/api/tasks")
def tasks():
    with connect() as db: rows=db.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    result=[]
    for row in rows:
        item=dict(row); item["overdue"]=False
        if item["due_at"] and item["status"] not in ("completed","blocked"):
            try:
                due=datetime.fromisoforma…54 tokens truncated…               item["deadline_error"]="invalid ISO-8601 due_at"
        result.append(item)
    return result

@app.get("/api/handle-suggestions")
def handle_suggestions(brand:str):
    import re
    stem=re.sub(r"[^a-z0-9]+","_",brand.lower()).strip("_")[:22] or "brand"
    options=[f"{stem}_official",f"{stem}_team",f"{stem}_brand"]
    return {"suggestions":options,"availability":"not checked; operator must check manually on Instagram","platform_contacted":False}

@app.post("/api/tasks",status_code=201)
def create_task(body:TaskIn,request:Request):
    with connect() as db:
        if not db.execute("SELECT 1 FROM accounts WHERE id=?",(body.account_id,)).fetchone():
            raise HTTPException(404,detail={"code":"ACCOUNT_NOT_FOUND","message":"Account record not found."})
        row=db.execute("SELECT * FROM tasks WHERE idempotency_key=?",(body.idempotency_key,)).fetchone()
        if row:return {**dict(row),"deduplicated":True}
        task_id=str(uuid.uuid4()); timestamp=now()
        db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)",(task_id,body.idempotency_key,body.account_id,body.title,body.owner,body.due_at,"open",body.instructions,None,timestamp,timestamp))
        row=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
    record_event("human_task_created",{"task_id":task_id,"title":body.title},request.state.correlation_id)
    return dict(row)

@app.patch("/api/tasks/{task_id}")
def update_task(task_id:str,body:TaskUpdate,request:Request):
    with connect() as db:
        task=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
        if not task:
            raise HTTPException(404,detail={"code":"TASK_NOT_FOUND","message":"Task not found."})
        if task["idempotency_key"].startswith(f"provisioning:{task['account_id']}:"):
            current_step=task["idempotency_key"].rsplit(":",1)[-1]
            index=next((i for i,s in enumerate(PROVISIONING_STEPS) if s["step_id"]==current_step),None)
            if index is not None and index>0:
                prior_keys=[f"provisioning:{task['account_id']}:{s['step_id']}" for s in PROVISIONING_STEPS[:index]]
                placeholders=",".join("?" for _ in prior_keys)
                prior=db.execute(f"SELECT count(*) FROM tasks WHERE idempotency_key IN ({placeholders}) AND status='completed'",prior_keys).fetchone()[0]
                if body.status!="blocked" and prior!=len(prior_keys):
                    raise HTTPException(409,detail={"code":"PREREQUISITE_NOT_COMPLETE","message":"Complete the previous provisioning step before advancing."})
            if task["status"]=="blocked" and body.status in ("in_progress","completed"):
                raise HTTPException(409,detail={"code":"TASK_BLOCKED","message":"Reopen the task after its blocker is cleared before completing it."})
        db.execute("UPDATE tasks SET status=?,evidence=?,updated_at=? WHERE id=?",(body.status,body.evidence,now(),task_id))
        if body.status=="completed" and task["idempotency_key"].startswith(f"provisioning:{task['account_id']}:"):
            current_step=task["idempotency_key"].rsplit(":",1)[-1]
            index=next((i for i,s in enumerate(PROVISIONING_STEPS) if s["step_id"]==current_step),None)
            if index is not None and index+1<len(PROVISIONING_STEPS):
                next_key=f"provisioning:{task['account_id']}:{PROVISIONING_STEPS[index+1]['step_id']}"
                db.execute("UPDATE tasks SET status='open',updated_at=? WHERE idempotency_key=? AND status='blocked'",(now(),next_key))
        row=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
    record_event("human_task_updated",{"task_id":task_id,"status":body.status},request.state.correlation_id)
    return dict(row)

@app.post("/api/audits/run")
def audit(request:Request):
    return run_audit(request.state.correlation_id)

@app.get("/api/findings")
def findings():
    with connect() as db: rows=db.execute("SELECT * FROM findings ORDER BY created_at DESC").fetchall()
    return [dict(row) for row in rows]

@app.get("/api/offboarding/{account_id}/{person}")
def offboarding(account_id:str,person:str):
    with connect() as db:
        if not db.execute("SELECT 1 FROM accounts WHERE id=?",(account_id,)).fetchone():
            raise HTTPException(404,detail={"code":"ACCOUNT_NOT_FOUND","message":"Account record not found."})
    return {"account_id":account_id,"departing_person":person,"completed":[],"pending":["Verify and remove roles through Meta Business Suite or supported integration.","Rotate accessible credentials through the approved vault.","Replace exposed backup codes and update the register."],"blocked":["Company test environment and Meta authorization were not supplied; no live changes were made."],"evidence_label":"unverified"}

@app.post("/api/offboarding/{account_id}/tasks")
def create_offboarding_tasks(account_id:str,body:OffboardingIn,request:Request):
    actions=[
      ("remove_roles",f"Remove {body.departing_person}'s roles from test business assets","Use Meta Business Suite or supported integration; record redacted confirmation. This app does not change roles."),
      ("rotate_credentials",f"Rotate credentials accessible to {body.departing_person}","Rotate through the approved vault and authorized human process. Never put credential values in task evidence."),
      ("replace_backup_codes",f"Replace backup codes exposed to {body.departing_person}","Regenerate through the official account security flow and store new values directly in the approved vault."),
      ("reconcile_register",f"Reconcile account register after offboarding {body.departing_person}","Update least-privilege roles, vault references, status, evidence provenance, and last verification date after confirmation.")]
    output=[]
    with connect() as db:
        if not db.execute("SELECT 1 FROM accounts WHERE id=?",(account_id,)).fetchone():
            raise HTTPException(404,detail={"code":"ACCOUNT_NOT_FOUND","message":"Account register record not found."})
        for action,title,instructions in actions:
            key=f"offboarding:{account_id}:{body.departing_person.casefold()}:{action}"
            row=db.execute("SELECT * FROM tasks WHERE idempotency_key=?",(key,)).fetchone()
            deduplicated=bool(row)
            if not row:
                task_id=str(uuid.uuid4()); timestamp=now()
                details="Human-only action; do not proceed without company authorization. "+instructions
                db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?,?)",(task_id,key,account_id,title,body.owner,body.due_at,"open",details,None,timestamp,timestamp))
                row=db.execute("SELECT * FROM tasks WHERE id=?",(task_id,)).fetchone()
            output.append({**dict(row),"deduplicated":deduplicated})
    record_event("offboarding_tasks_created",{"account_id":account_id,"task_count":len(output),"live_changes":False},request.state.correlation_id)
    return {"account_id":account_id,"departing_person":body.departing_person,"tasks":output,"live_changes":False,"evidence_label":"unverified"}

@app.get("/api/proxy/policy")
def proxy_policy():
    return {"status":"not_configured","credential_storage":"approved vault only; references only in app","health_check":"not run: approved proxy reference and neutral endpoint not supplied","session_policy":"preserve stable connections during active work; rotate for planned maintenance or confirmed proxy failure, never to evade controls","challenge_policy":"pause and request human review","evidence_label":"unverified"}

@app.post("/api/proxy/simulate-failover")
def simulate_proxy_failover(body:ProxySimulationIn,request:Request):
    """Deterministic local control-flow demo; makes no proxy or network connection."""
    max_attempts=3  # initial attempt plus at most two bounded retries
    attempts=[]
    primary_succeeds=body.primary_failures < max_attempts
    if body.security_challenge:
        attempts.append({"connection":"synthetic-primary","attempt":1,"result":"security_challenge_fixture","retry":False})
        outcome="paused_for_human_review"
        selected=None
    else:
        for attempt in range(1,min(body.primary_failures,max_attempts)+1):
            attempts.append({"connection":"synthetic-primary","attempt":attempt,"result":"timeout_fixture","backoff_seconds":0 if attempt==max_attempts else round(0.25*(2**(attempt-1)),2),"retry":attempt<max_attempts})
        if primary_succeeds:
            attempts.append({"connection":"synthetic-primary","attempt":body.primary_failures+1,"result":"healthy_fixture","retry":False})
            outcome="primary_healthy"
            selected="synthetic-primary"
        elif body.secondary_healthy:
            attempts.append({"connection":"synthetic-secondary","attempt":1,"result":"healthy_fixture","retry":False})
            outcome="controlled_failover_succeeded"
            selected="synthetic-secondary"
        else:
            attempts.append({"connection":"synthetic-secondary","attempt":1,"result":"unhealthy_fixture","retry":False})
            outcome="failover_unavailable"
            selected=None
    record_event("proxy_failover_simulated",{"outcome":outcome,"attempt_count":len(attempts),"network_access":False},request.state.correlation_id)
    return {"mode":"deterministic synthetic simulation","neutral_endpoint_contacted":False,"proxy_credentials_used":False,"outcome":outcome,"selected_connection":selected,"attempts":attempts,"max_primary_attempts":max_attempts,"rotation_reason":"simulated repeated primary failures on a neutral test scenario" if outcome=="controlled_failover_succeeded" else "none","security_challenge_policy":"pause; do not rotate or retry" if body.security_challenge else "no challenge fixture","evidence_label":"unverified"}

@app.get("/api/events")
def events():
    with connect() as db: rows=db.execute("SELECT * FROM audit_events ORDER BY id DESC LIMIT 100").fetchall()
    return [dict(row) for row in rows]
