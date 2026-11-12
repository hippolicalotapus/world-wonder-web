# Private editorial backup and recovery

This is an offline command-line facility, not a hosted backup service.
Keep the private source, snapshots, and restored files outside the public
website and Git repository. A checksum detects accidental changes but is
not encryption or authentication. Protect sensitive files with filesystem
permissions and appropriate encrypted storage.

```sh
python3 tools/editorial_backup.py create /private/editorial.json /private/backups/snapshot-001.json
python3 tools/editorial_backup.py verify /private/backups/snapshot-001.json
python3 tools/editorial_backup.py restore /private/backups/snapshot-001.json /private/editorial-restored.json --receipt /private/recovery-receipt-001.json
```

Backup and restore destinations must have existing parent directories,
must not exist already, and must not be symlinks. Writes are create-only
and owner-readable on POSIX systems. Restore validates the entire
record collection and checks SHA-256 before writing to a new private file.
Review the restored records before using them for subsequent editorial
decisions. This tool does not modify `public-catalogue.json`.

## Recovery provenance
A successful restore writes a separate owner-only receipt containing the
verified backup checksum, backup creation timestamp, restoration timestamp,
and number of restored records. It contains no article text, reviewer names,
or private evidence. Keep receipts in private storage alongside recovery
records. A receipt is an integrity record, not a cryptographic signature or
proof of the identity of the person who restored the backup.

## Interrupted recovery handling
The restore command checks that both destination paths are available before
writing. If the receipt write fails normally, it removes the newly restored
record file so the operation can be retried with fresh paths. This is
compensating cleanup, **not** a crash-atomic two-file transaction. If power
fails or the process is forcibly terminated between writes, inspect the
private directory and verify the restored data and receipt before continuing.
Never assume an absent receipt means a completed recovery.

## Read-only reconciliation
After an unexpected interruption, run:

```sh
python3 tools/reconcile_recovery.py /private/backups/snapshot-001.json /private/editorial-restored.json /private/recovery-receipt-001.json
```

The checker returns `verified`, `not_started`, or a specific missing,
invalid, or mismatched status. It never modifies files, prints private
record content, or automatically deletes an incomplete recovery. A missing
receipt is **not** proof that the restored data is safe to use. Investigate
and manually reconcile private files before continuing editorial work.
