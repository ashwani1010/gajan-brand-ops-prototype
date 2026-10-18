"""Human-only, sequential account provisioning checklist."""

PROVISIONING_STEPS = [
    {
        "step_id": "authorization",
        "title": "Confirm company authorization and test resources",
        "instructions": "Confirm written approval for this exact throwaway brand, test email and company-controlled phone, separate Meta business, approved vault, and proxy scope. The assignment says these resources are provided, but none were supplied here. Until available, mark this task blocked. Do not substitute a personal or production account.",
    },
    {
        "step_id": "handle",
        "title": "Choose a handle and check availability manually",
        "instructions": "Review the app's suggested handles. A human must check availability in the official Instagram app/site. Suggestions do not check or reserve handles. Record the chosen handle and redacted evidence.",
    },
    {
        "step_id": "recovery_contacts",
        "title": "Request the company email alias and assign the test phone",
        "instructions": "Use the company's authorized owner to create/request the alias and reserve/assign its company-controlled phone. Do not use personal recovery details. Record masked contact details and owner in the register; never enter verification codes here.",
    },
    {
        "step_id": "signup",
        "title": "Create the test account manually",
        "instructions": "Only after authorization and approved test resources are confirmed, a human operator uses the official Instagram app/site to create the one throwaway brand account. Do not use scripts, browser automation, emulators, proxies for signup, or account farms. Stop on any challenge or restriction and request human review.",
    },
    {
        "step_id": "verification",
        "title": "Complete email and phone verification manually",
        "instructions": "The authorized human operator reads verification codes from the company-controlled test channels and enters them directly in the official Instagram interface. Never share codes in this app, logs, reports, or chat. Do not bypass challenges.",
    },
    {
        "step_id": "security",
        "title": "Enable two-factor authentication and save recovery material",
        "instructions": "A human enables 2FA in account settings. Store the password and backup codes directly in the approved vault. Put only vault item references in the register. Do not paste secret values into this app or completion evidence.",
    },
    {
        "step_id": "profile",
        "title": "Complete the profile manually",
        "instructions": "Set the approved display name, bio of at most 150 characters, link, category, and image using the official interface. Then record the values and a redacted human-confirmation note in the register. The register endpoint does not change Instagram.",
    },
    {
        "step_id": "business_link",
        "title": "Convert to business and link Meta assets",
        "instructions": "A human follows supported Meta/Instagram workflows to convert the account, link Business Suite/Business Manager, and assign only the requested least-privilege people and roles. Stop for review on any restriction. Do not claim an integration-verified status without integration evidence.",
    },
    {
        "step_id": "reconcile",
        "title": "Reconcile the register and capture walkthrough evidence",
        "instructions": "Compare account state to the register, record provenance and last verification date, list remaining blockers, and prepare the required 2–3 minute walkthrough. Redact secrets and personal contact details. Never present synthetic records as live evidence.",
    },
]
