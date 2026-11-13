"""Produce an offline operator checklist for interrupted private receipt files.

This tool does not read, rename, or remove any receipt file.
"""
from tools.receipt_temp_review import plan_receipt_temp_review

def receipt_recovery_checklist(directory):
    plan=plan_receipt_temp_review(directory)
    checklist=[]
    for entry in plan["files"]:
        checklist.append({
            "name":entry["name"],
            "classification":entry["kind"],
            "manual_actions":["Verify writer has stopped","Check private receipt destination and backups","Obtain explicit approval before cleanup"],
            "automatic_cleanup_allowed":False
        })
    return {"checklist":checklist,"requires_operator":bool(checklist),"files_modified":0}
