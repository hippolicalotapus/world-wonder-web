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
