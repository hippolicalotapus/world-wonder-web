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
