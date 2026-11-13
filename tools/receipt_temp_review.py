"""Read-only plan for interrupted private receipt temp files.

Never reads receipt contents or deletes files. Operators must inspect and
authorize any cleanup separately. This is not a recovery or deletion command.
"""
from tools.inspect_receipt_temps import inspect_receipt_temps

def plan_receipt_temp_review(directory):
    entries=inspect_receipt_temps(directory)
    return {
        "files":entries,
        "review_required":bool(entries),
        "safe_to_auto_delete":False,
        "operations_performed":0,
        "recommendation":"Review each interrupted private receipt and backup state manually before any cleanup" if entries else "No interrupted receipt temporary files detected"
    }
