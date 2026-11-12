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
