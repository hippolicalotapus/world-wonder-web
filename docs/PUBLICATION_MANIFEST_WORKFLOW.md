# Offline publication manifest workflow

The preparation tool only creates or validates a **private** manifest.
It does not publish, deploy, modify the public catalogue, or authenticate
reviewers. Store the editorial source and manifest outside the website
and Git repository.

```sh
python3 tools/publication_manifest.py prepare /private/editorial.json /private/manifest-001.json
python3 tools/publication_manifest.py validate /private/editorial.json /private/manifest-001.json
```

Preparation validates the editorial records and source rights, computes a
SHA-256 digest of canonical source JSON, and lists every record explicitly
marked `published`. The manifest is written to a new private file, never
overwriting an existing manifest. Validation rejects changed sources,
unexpected publication IDs, and invalid published records.

Review the manifest and proposed published records independently before
using the separate public export command. A digest is not a signature,
authentication, or approval by itself. No records are made public by
running this tool.

## Independent publication sign-off
Public export now requires a separate private `world-wonder-independent-review-v1`
attestation bound to the manifest checksum. The named independent reviewer
must differ from the reviewer recorded as approving or publishing each
published record. A missing approval history blocks export. Export writes
only a **new** `public-catalogue.json` file and refuses overwriting an
existing file; it does not deploy or publish to the website automatically.
The attestation format is an offline procedural check, **not** authenticated
identity or a digital signature. Never treat a self-entered reviewer name
as proof of independent human review. Keep private attestations outside Git.

## Prepare an independent review attestation offline
After a separate reviewer has actually inspected the source and manifest:

```sh
python3 tools/reviewer_attestation.py prepare /private/editorial.json /private/manifest-001.json /private/review-001.json --reviewer "Independent Editor"
python3 tools/reviewer_attestation.py validate /private/editorial.json /private/manifest-001.json /private/review-001.json
```

The tool refuses an approving editor's name, changed source records,
symlink inputs, and overwriting an existing private attestation. It does
not publish, deploy, or independently establish the reviewer's identity.
Human review is still required; do not generate an attestation merely to
satisfy the software gate.

## Final public artifact privacy check
Before writing a new public catalogue, the exporter now checks the exact
public record and source field sets, published status, unique IDs, required
sources, evidence classification, source dates, URL schemes and embedded URL
credentials. Unexpected internal fields are rejected rather than silently
written. The existing JavaScript CI artifact check remains in place as a
second, independent gate. The exporter still requires a source-bound
manifest and separate reviewer attestation and refuses to overwrite an
existing catalogue. These checks do not publish or deploy the website.

## Privacy-safe export receipt
The export CLI requires a fifth positional argument: a **new private receipt
path**, separate from `public-catalogue.json`. It creates a checksum-bound
receipt containing only the catalogue digest, record count and timestamp.
Both output paths must be new. Ordinary receipt-write failures trigger
cleanup of the newly created catalogue; a process crash between writes
still requires manual reconciliation. Keep receipts out of the public
website and Git repository. No deployment is performed by the CLI.

## Reconcile interrupted exports (read-only)
Run the checker against a prepared catalogue and its private receipt:

```sh
python3 tools/reconcile_public_export.py /private/export/public-catalogue.json /private/export-receipt.json
```

The command prints `verified`, `not_started`, `missing_catalogue`,
`missing_receipt`, `invalid_catalogue`, `invalid_receipt`,
`receipt_mismatch`, or `unreadable_or_invalid_file`. It never writes,
repairs, publishes, or prints private content. Missing or mismatched files
require manual inspection and a new reviewed export, not automatic repair.
Forcible process termination can still leave a catalogue without its
receipt; the reconciliation command detects this state.

## Concurrent file replacement protection
The create-only writer links a fully flushed temporary file into place
without replacing an existing destination and syncs the containing directory
on POSIX systems. If receipt creation fails, cleanup checks the identity of
the catalogue file it created before removing it, avoiding deletion of a
concurrently replaced file. This is not a crash-atomic transaction, nor a
complete defense against hostile processes with write access to the output
directory. Keep output directories access-controlled and use the read-only
reconciliation command after any interruption.

## Private input file safety
Manifest preparation, reviewer attestation, and the public export CLI use a
shared read-only loader for private JSON. It refuses symbolic links, named
pipes, directories and a file named `public-catalogue.json` as private
inputs. On systems supporting `O_NOFOLLOW`, the file is opened without
following a final symlink. These checks reduce accidental disclosure and
blocking reads; they are not a substitute for restricted private-directory
permissions or authenticated reviewer access.

## Private/public output separation
The public export command now requires private editorial inputs and the
private audit receipt to reside outside the public catalogue's directory.
All five input/output paths must be distinct, and output files must not
already exist. Use an existing, access-controlled private directory for
source records, manifest, reviewer attestation and receipt; use a separate
staging directory for the new `public-catalogue.json`. This reduces the
risk of publishing a private receipt or editorial source by copying an
entire export directory. This path check does not replace filesystem
permissions or deployment review, and no deployment occurs automatically.

## Independent approval chronology
Independent-review attestation validation now requires a nonblank named
editorial approver and timezone-aware approval timestamp for each approval
or publication history entry. A purported independent review that predates
editorial approval is rejected. Reviewer names are compared without case,
so changing capitalization does not bypass the two-person procedural check.
These checks do not authenticate users or establish that a human review
actually happened. Keep review histories private and independently audited.

## Review-history integrity at export approval
Before accepting independent reviewer attestation, the offline gate now checks
recorded editorial transitions against the allowed state machine, verifies
adjacent history entries connect, requires nonempty reasons, and checks
chronological ordering of timezone-aware timestamps. Legacy histories may
begin partway through the workflow, but any entries present must be coherent.
This detects inconsistent or accidentally altered histories; it does **not**
provide cryptographic tamper evidence or authenticate reviewers. Keep the
private audit log access-controlled and retain original backups.

## Optional hash-linked editorial audit history
Private editorial review histories may now be sealed with
`tools/review_audit_chain.py` using SHA-256 links between entries. The
independent approval gate validates these links whenever a sealed history
is present, rejecting altered, missing, reordered or mixed sealed entries.
Existing unsealed histories remain supported for backward compatibility.
Retain the final hash in a separately trusted, access-controlled location;
without that external anchor, someone able to rewrite the history can also
recompute all its hashes. This is tamper-evidence, not a digital signature,
reviewer authentication, or automatic proof of editorial approval. No public
website files or deployments are changed by sealing a private history.

## Trusted audit-anchor verification at export
The offline public exporter accepts an optional sixth argument,
`TRUSTED_ANCHORS.json`, after the private receipt path. When supplied,
it checks the separately retained `world-wonder-review-anchors-v1`
record-ID-to-head-hash mapping against all sealed editorial histories.
Missing or altered anchors, unsealed nonempty histories, and published
records without anchors block the export. Anchor input must be a distinct
private file outside the public catalogue directory.

To prepare the anchor data programmatically, use
`review_anchor_guard.prepare_anchors(records)` only **after** a real
editorial review. Retain its output separately from editable records and
protect it against unauthorized replacement. Recreating the anchor from
possibly compromised records defeats the tamper-evidence check. Existing
exports without this optional argument remain supported; those exports
**do not** gain trusted-anchor verification. This mechanism is not a
signature, reviewer authentication, or a substitute for access controls.

## Offline trusted audit-anchor commands
After reviewing and sealing private editorial histories, prepare a new anchor
in a separately controlled private directory (never inside Git or the public
website):

```sh
python3 tools/review_anchor_cli.py prepare /private/editorial/records.json /private/vault/anchor-001.json
python3 tools/review_anchor_cli.py verify /private/editorial/records.json /private/vault/anchor-001.json
```

Preparation is create-only, refuses an anchor alongside editable source
records, and refuses Git repositories and unsealed published histories.
Verification is read-only. Retain the resulting anchor under independent
access controls; merely creating it beside editable records does not establish
trust. Neither command publishes or deploys content.

## Audit-anchor path and hash hardening
Anchor preparation rejects output paths with symbolic-link ancestor directories,
including aliases of the editable source directory, and refuses Git repository
locations. Anchor verification requires nonempty record identifiers and
lowercase 64-character SHA-256 head hashes. Keep anchors in a separately
controlled private directory. These filesystem preflight checks cannot
protect against a hostile process changing directory entries concurrently;
use trusted filesystem permissions and retain independently verified copies.

## Mandatory anchors for sealed publication histories
The public export command now **requires** the optional trusted-anchor file
argument whenever any record marked `published` has a hash-sealed editorial
review history. Missing or mismatched anchors block export before a public
catalogue or receipt is written. Legacy exports with only unsealed review
histories still work without anchors. Sealed draft histories do not require
anchors unless an anchor file is explicitly supplied. Supplying an anchor
file requests strict verification of all included review histories; a mixed
legacy/sealed collection may need migration to fully sealed histories first.
This preserves old data but does not authenticate the human reviewer or
make unsealed legacy records tamper-evident.

## Safe legacy review-history migration
Older published records with valid, unsealed review histories can be migrated
without changing their original editorial decisions, status, or source file.
First inspect a dry run:

```sh
python3 tools/migrate_legacy_reviews.py /private/editorial/records.json
```

To create a separate, new private copy after review:

```sh
python3 tools/migrate_legacy_reviews.py /private/editorial/records.json --confirm-create --output /private/vault/migrated-records.json
```

The migration validates review transitions and chronology, preserves drafts,
rejects missing histories, and refuses to overwrite files. It does **not**
independently attest that old approvals were genuine. After migration, use
independent editorial review, separately retain trusted anchors for the new
sealed histories, and prepare a fresh manifest and attestation for the new
source digest before any public export. Do not silently replace existing
published records or treat migration as automatic authorization to publish.

## Privacy-safe legacy migration receipts
Confirmed legacy migration now requires both `--output` and `--receipt`, in
separate new private directories. It writes a new sealed copy and a minimal
receipt with only the source SHA-256, migrated SHA-256, record count, and
migrated count. Original records remain unchanged. Example:

```sh
python3 tools/migrate_legacy_reviews.py /private/source/records.json --confirm-create --output /private/migrated/records.json --receipt /private/receipts/migration.json
python3 tools/verify_migration.py /private/source/records.json /private/migrated/records.json /private/receipts/migration.json
```

Verification is read-only and checks that the migrated records are exactly
what the migration algorithm would produce. The receipt has no reviewer
identities or editorial text. A normal receipt-write failure attempts to
remove the new migrated file only if it has not been replaced; a process crash
can leave a partial pair that requires manual reconciliation. Protect all
three private files with separate access controls. Receipt hashes establish
consistency, not reviewer identity or independent approval. Fresh editorial
authorization and trusted anchors are still required before publication.

## Interrupted migration reconciliation
If migration was interrupted, run the read-only reconciliation command before
retrying or moving any private files:

```sh
python3 tools/reconcile_migration.py /private/source/records.json /private/migrated/records.json /private/receipts/migration.json
```

It reports `not_started`, `missing_receipt`, `orphaned_receipt`, or
`verified_complete`. For a missing receipt, it first verifies that the
migrated file exactly matches the expected migration; a mismatched or
malformed file is rejected instead of being called recoverable. An existing
receipt must match the source and migrated file hashes. The command never
creates, removes, or overwrites any file. Incomplete states return a nonzero
exit code; keep them quarantined for manual review and use fresh paths for
any later attempt. A verified pair is not itself publication authorization.

## Explicit recovery of a missing migration receipt
When read-only reconciliation reports `missing_receipt`, and only after
independently checking the original and migrated private files, the receipt
may be created with:

```sh
python3 tools/recover_migration_receipt.py /private/source/records.json /private/migrated/records.json /private/receipts/migration.json --confirm-create
python3 tools/verify_migration.py /private/source/records.json /private/migrated/records.json /private/receipts/migration.json
```

Recovery requires explicit confirmation, a verified matching migration, a
new receipt path in a separate private directory, and refuses overwrites.
It rechecks both inputs before writing and does not change either source
file. Do not use this to repair mismatched migrations, orphaned receipts, or
published data. Filesystem changes by a hostile concurrent writer remain a
risk without exclusive directory access; this is not publication approval.

## Concurrent-change detection for private migration inputs
Receipt recovery and independent receipt verification now capture private
input file identity, size, and nanosecond modification/change timestamps,
then reread inputs to detect changes before completing the operation.
Symlinked private input files are refused. The checks detect ordinary
concurrent edits and file replacement but do not establish exclusive locks
or eliminate time-of-check/time-of-use races against hostile writers. Use
exclusive access to private storage during recovery and verification. No
public website files are modified by these checks.

## Advisory locking during private recovery
The receipt recovery and independent verification commands now acquire
nonblocking POSIX shared advisory locks on private input file descriptors,
reject symlinks and non-regular inputs, and check file identity and metadata
again before releasing locks. A competing exclusive advisory lock causes
recovery to fail closed. This works only where POSIX `fcntl.flock` is
available and cooperating writers respect the same locking convention.
Advisory locks do not stop hostile or uncooperative writers, nor do they
prevent directory-entry races. Use access-controlled private storage and
exclusive operational access for sensitive recovery; never interpret a
verified receipt as publication approval. No website files are changed.
