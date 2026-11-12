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
