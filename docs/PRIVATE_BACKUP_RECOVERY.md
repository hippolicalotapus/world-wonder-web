# Private editorial backup and recovery

This is an offline command-line facility, not a hosted backup service.
Keep the private source, snapshots, and restored files outside the public
website and Git repository. A checksum detects accidental changes but is
not encryption or authentication. Protect sensitive files with filesystem
permissions and appropriate encrypted storage.

```sh
python3 tools/editorial_backup.py create /private/editorial.json /private/backups/snapshot-001.json
python3 tools/editorial_backup.py verify /private/backups/snapshot-001.json
python3 tools/editorial_backup.py restore /private/backups/snapshot-001.json /private/editorial-restored.json
```

Backup and restore destinations must have existing parent directories,
must not exist already, and must not be symlinks. Writes are create-only
and owner-readable on POSIX systems. Restore validates the entire
record collection and checks SHA-256 before writing to a new private file.
Review the restored records before using them for subsequent editorial
decisions. This tool does not modify `public-catalogue.json`.
