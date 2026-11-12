# Private editorial review console

The local-only console is a command-line tool for editorial staff, not a public
web page or an authenticated production dashboard. Do not upload its private
input or output files to the public website, commit them to Git, or expose
them in static hosting.

Use a private file outside the repository:

```sh
python3 tools/review_console.py /private/editorial-records.json queue
sha256sum /private/editorial-records.json
python3 tools/review_console.py /private/editorial-records.json decide --id example-id --state fact_check --expected-status draft --expected-sha256 YOUR_SHA256 --reviewer "Editor" --reason "Research started" --output /private/editorial-next.json
```

The queue lists IDs and statuses only. A decision validates the entire
result, requires an allowed state transition, records reviewer, reason and
timezone-aware timestamp, and writes a separate owner-only JSON file.
Approval and publication are blocked unless publication requirements pass.
The public catalogue remains unchanged until an independent, validated
export is explicitly prepared and reviewed.

This is not a multi-user authorization system. Local filesystem access
controls must protect private editorial data. Do not use it as a network
service or deploy it. Real reviewer authentication and approvals remain
future milestones.

The decision command requires the reviewed input file SHA-256 and the expected
current review state. This prevents accepting decisions based on stale
information. Outputs are create-only by default and refuse overwriting
existing files. Choose a new private output path for each decision.
