import os
import requests
import streamlit as st
from datetime import datetime, timedelta

API=os.getenv("API_BASE_URL","http://localhost:8000")
st.set_page_config(page_title="Brand Ops Console",layout="wide")
st.title("Brand Operations Console")
st.caption("Local prototype • synthetic seed records • no Instagram automation or live company integration")

def get(path):
    try:
        response=requests.get(API+path,timeout=4)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error("API unavailable. Start FastAPI and check API_BASE_URL.")
        return []

register,tasks_tab,audit_tab,offboarding,proxy,provisioning=st.tabs(["Register","Human tasks","Audit","Offboarding","Proxy & evidence","Provisioning guide"])
with register:
    st.subheader("Account register")
    with st.expander("Suggest candidate handles (availability must be checked manually)"):
        brand=st.text_input("Brand name",value="Northstar Test Brand")
        if st.button("Suggest handles"):
            try:
                response=requests.get(API+"/api/handle-suggestions",params={"brand":brand},timeout=4)
                response.raise_for_status()
                st.json(response.json())
            except requests.RequestException: st.error("API unavailable; no availability check was performed.")
    rows=get("/api/accounts")
    if rows: st.dataframe(rows,use_container_width=True,hide_index=True)
    st.info("Recovery details are masked. Vault values are never displayed; demo vault references are synthetic.")
    if rows:
        st.write("Record profile details after a human completes the platform steps")
        account_ids={f"{row['brand']} ({row['id']})":row["id"] for row in rows}
        with st.form("profile_record"):
            selected=st.selectbox("Account",list(account_ids))
            profile_name=st.text_input("Profile name")
            bio=st.text_area("Bio (maximum 150 characters)",max_chars=150)
            link=st.text_input("Profile link")
            category=st.text_input("Category")
            image_ref=st.text_input("Image reference (vault/storage reference only)")
            evidence_note=st.text_input("Redacted human confirmation note")
            if st.form_submit_button("Record profile fields as unverified"):
                try:
                    response=requests.patch(API+f"/api/accounts/{account_ids[selected]}/profile",json={"profile_name":profile_name,"bio":bio,"profile_link":link,"category":category,"image_ref":image_ref,"evidence_note":evidence_note},timeout=4)
                    if response.ok: st.success("Register updated as unverified. Instagram itself was not changed.")
                    else: st.error(f"Register update failed: HTTP {response.status_code}")
                except requests.RequestException: st.error("API unavailable; register was not updated.")
with tasks_tab:
    st.subheader("Human tasks")
    current=get("/api/tasks")
    if current: st.dataframe(current,use_container_width=True,hide_index=True)
    with st.form("new_task"):
        st.write("Create a human-owned handoff")
        account=st.text_input("Account ID",value="demo-findings")
        key=st.text_input("Idempotency key",value="demo-signup-handoff-v1")
        title=st.text_input("Task",value="Complete signup and verification manually")
        owner=st.text_input("Owner",value="Company test operator")
        due=st.text_input("Deadline (ISO-8601)",value="")
        instructions=st.text_area("Instructions",value="Use the authorized test environment. Do not automate signup or verification.")
        if st.form_submit_button("Create human task"):
            try:
                response=requests.post(API+"/api/tasks",json={"account_id":account,"idempotency_key":key,"title":title,"owner":owner,"due_at":due or None,"instructions":instructions},timeout=4)
                if response.ok: st.success("Task saved. Repeated submissions with the same key are deduplicated.")
                else: st.error(f"Task not saved: HTTP {response.status_code}")
            except requests.RequestException: st.error("API unavailable; task was not saved.")
    if current:
        st.write("Update a human task after the owner completes or blocks it")
        task_ids={f"{item['title']} — {item['id'][:8]}":item["id"] for item in current}
        with st.form("update_task"):
            selected=st.selectbox("Task",list(task_ids))
            status=st.selectbox("Status",["in_progress","completed","blocked","open"])
            evidence=st.text_area("Redacted completion evidence",max_chars=1000)
            if st.form_submit_button("Save task status"):
                try:
                    response=requests.patch(API+"/api/tasks/"+task_ids[selected],json={"status":status,"evidence":evidence or None},timeout=4)
                    if response.ok: st.success("Task updated.")
                    else: st.error(f"Update failed: HTTP {response.status_code}")
                except requests.RequestException: st.error("API unavailable; task was not updated.")
    st.caption("Overdue status is derived from the saved deadline. Reminder delivery and escalation need an authorized scheduler/notification integration and are not configured.")
with audit_tab:
    st.subheader("Weekly audit")
    st.write("The schedule is documented; run-on-demand is available for the local register.")
    if st.button("Run audit now"):
        try:
            response=requests.post(API+"/api/audits/run",timeout=8)
            response.raise_for_status()
            st.session_state.audit=response.json()
        except requests.RequestException: st.error("Audit request failed; check API availability.")
    if "audit" in st.session_state: st.json(st.session_state.audit)
    current=get("/api/findings")
    if current: st.dataframe(current,use_container_width=True,hide_index=True)
with offboarding:
    st.subheader("Offboarding plan")
    account=st.text_input("Account ID",value="demo-findings",key="offboarding_account")
    person=st.text_input("Departing test member",value="Departing Member")
    owner=st.text_input("Task owner",value="Candidate operator",key="offboarding_owner")
    deadline=st.text_input("Task deadline (ISO-8601 with timezone)",placeholder="YYYY-MM-DDTHH:MM:SS+05:30",key="offboarding_deadline")
    if st.button("Create human offboarding tasks"):
        try:
            response=requests.post(f"{API}/api/offboarding/{account}/tasks",json={"departing_person":person,"owner":owner,"due_at":deadline},timeout=4)
            if response.ok:
                data=response.json()
                st.success(f"Created or reused {len(data['tasks'])} human tasks. No roles or credentials were changed.")
                st.json(data)
            else: st.error(f"Offboarding tasks not created: HTTP {response.status_code}")
        except requests.RequestException: st.error("Could not create offboarding tasks.")
    if st.button("View offboarding status"):
        try:
            response=requests.get(f"{API}/api/offboarding/{account}/{person}",timeout=4)
            response.raise_for_status()
            st.json(response.json())
        except requests.RequestException: st.error("Could not retrieve offboarding status.")
    st.warning("This is a checklist only. It does not change roles, credentials, or backup codes.")
with proxy:
    st.subheader("Proxy policy and run evidence")
    st.json(get("/api/proxy/policy"))
    st.info("The proxy simulation below runs only fixed synthetic outcomes. It uses no real proxy, credential, external endpoint, or Instagram connection.")
    with st.form("proxy_simulation"):
        failures=st.number_input("Synthetic primary failures before failover",min_value=0,max_value=5,value=3)
        secondary=st.checkbox("Synthetic secondary connection healthy",value=True)
        challenge=st.checkbox("Simulate a security challenge (must pause)",value=False)
        if st.form_submit_button("Run synthetic failover simulation"):
            try:
                response=requests.post(API+"/api/proxy/simulate-failover",json={"primary_failures":int(failures),"secondary_healthy":secondary,"security_challenge":challenge},timeout=4)
                response.raise_for_status()
                st.json(response.json())
            except requests.RequestException: st.error("Simulation failed; check API availability.")
    st.write("Recent redacted operational events")
    current=get("/api/events")
    if current: st.dataframe(current,use_container_width=True,hide_index=True)
with provisioning:
    st.subheader("Human-led account provisioning")
    st.warning("This workflow creates register records and tasks only. It does not create an Instagram account. The assignment requires company authorization and a human to perform signup and verification.")
    st.write("If the promised company test brand, test email/phone, vault, Meta business, or approved proxy are unavailable, stop at step 1 and mark later tasks blocked. Do not substitute a personal or production account.")
    steps=get("/api/provisioning/steps")
    if isinstance(steps,dict):
        for index,step in enumerate(steps.get("steps",[]),1):
            with st.expander(f"{index}. {step['title']}"):
                st.write(step["instructions"])
    with st.expander("Create a local register placeholder after you know the authorized test brand"):
        with st.form("new_account_register"):
            brand=st.text_input("Authorized test brand name")
            handle=st.text_input("Chosen handle (manual availability check required)")
            owner=st.text_input("Account owner",value="Candidate operator")
            recovery_email=st.text_input("Company recovery email (optional; no passwords or codes)")
            recovery_phone=st.text_input("Company test phone (optional)")
            if st.form_submit_button("Create blocked/unverified register record"):
                try:
                    response=requests.post(API+"/api/accounts",json={"brand":brand,"handle":handle,"owner":owner,"recovery_email":recovery_email or None,"recovery_phone":recovery_phone or None},timeout=4)
                    if response.ok: st.success("Local register record created as blocked/unverified. No Instagram account was created.")
                    else: st.error(f"Register record not saved: HTTP {response.status_code}")
                except requests.RequestException: st.error("API unavailable; register record was not saved.")
    accounts=get("/api/accounts")
    if accounts:
        by_label={f"{item['brand']} — {item['handle']} [{'synthetic sample' if item['id'].startswith('demo-') else item['status']}]":item["id"] for item in accounts}
        with st.form("start_provisioning"):
            st.write("Create the tracked task sequence")
            selected=st.selectbox("Register record",list(by_label))
            owner=st.text_input("Task owner",value="Candidate operator")
            suggested_deadline=(datetime.now().astimezone()+timedelta(days=2)).replace(microsecond=0).isoformat()
            deadline=st.text_input("Task deadline (ISO-8601 with timezone)",value=suggested_deadline,help="Keep the full date and timezone offset, for example 2026-10-20T17:00:00+05:30.")
            if st.form_submit_button("Create nine human tasks"):
                try:
                    response=requests.post(API+f"/api/accounts/{by_label[selected]}/provisioning-workflow",json={"owner":owner,"due_at":deadline},timeout=6)
                    if response.ok:
                        result=response.json()
                        st.success(f"{result['task_count']} tracked tasks available. No platform actions were performed.")
                    else:
                        try:
                            details=response.json()
                            issues=details.get("detail",details)
                            st.error(f"Workflow not created (HTTP {response.status_code}): {issues}")
                        except ValueError:
                            st.error(f"Workflow not created (HTTP {response.status_code}): {response.text[:500]}")
                except requests.RequestException: st.error("API unavailable; workflow tasks were not created.")
