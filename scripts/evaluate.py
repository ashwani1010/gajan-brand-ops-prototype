"""Repeatable fixture consistency metrics; no external or live account access."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.audit import classify_account
cases=json.loads((ROOT/"evaluation/golden_audits.json").read_text())
fixtures={
 "clean_test_account":{"recovery_email":"owner@company.example.invalid","backup_codes_in_vault":True,"two_factor_enabled":True,"people_roles":[],"evidence_label":"unverified"},
 "non_company_recovery_and_missing_security":{"recovery_email":"owner@example.invalid","backup_codes_in_vault":False,"two_factor_enabled":False,"people_roles":[],"evidence_label":"unverified"},
 "stale_privileged_role":{"recovery_email":"owner@company.example.invalid","backup_codes_in_vault":True,"two_factor_enabled":True,"people_roles":[{"role":"Admin","last_verified":"2025-01-01"}],"evidence_label":"unverified"}}
tp=fp=fn=0
for case in cases:
    expected=set(case["expected"])
    predicted={finding["type"] for finding in classify_account(fixtures[case["case"]])}
    tp+=len(expected&predicted); fp+=len(predicted-expected); fn+=len(expected-predicted)
    print(f"{case['case']}: expected={sorted(expected)} predicted={sorted(predicted)} pass={expected==predicted}")
precision=tp/(tp+fp) if tp+fp else 1.0
recall=tp/(tp+fn) if tp+fn else 1.0
f1=2*precision*recall/(precision+recall) if precision+recall else 0.0
print(f"cases={len(cases)} labelled_findings={tp+fn} TP={tp} FP={fp} FN={fn}")
print(f"precision={precision:.3f} recall={recall:.3f} F1={f1:.3f}")
print("NOTE: These are fixture consistency metrics, not live-account or independent API test results.")
