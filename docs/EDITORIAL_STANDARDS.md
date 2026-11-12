# Editorial and evidence standard — World Wonder Web

Status: development policy, not a claim that published articles have been verified.

## Purpose
Explore extraordinary achievements, natural wonders, inspiring events, remarkable discoveries and reported miracles with curiosity and intellectual honesty.

## Source and verification requirements
- Each factual entry must include a stable title, subject category, publication/review date, at least one attributable source, and an evidence status.
- Prefer original research, museum or archive records, peer-reviewed studies, official data and reliable first-hand documentation.
- Clearly distinguish documented events, scientific hypotheses, faith-based interpretations, anecdotal accounts and unverified claims.
- For reported miracles, explain what is reported, by whom, what independent evidence exists and what remains unknown. Do not present disputed supernatural explanations as established facts.
- Never fabricate testimonials, images presented as authentic evidence, quotations or measurements.
- Link to sources rather than copying copyrighted text or imagery. Record licences and permissions for reuse.

## Respect and representation
- Treat cultures, religious traditions, communities and participants respectfully; seek context rather than extracting sensational stories.
- Protect private individuals and minors; obtain appropriate permissions for identifiable personal stories and images.
- Clearly label AI-generated illustrations as illustrations, never documentary evidence.
- Offer corrections and removal-request channels before launch.

## Entry lifecycle
1. Proposed — topic suggested, not verified.
2. Researching — sources gathered, claims under review.
3. Verified — documented facts checked, uncertainties labelled.
4. Published — editorial review passed.
5. Corrected/withdrawn — publicly document material changes.

## Release gates
- No public factual article without provenance and review.
- No membership billing until clear terms, cancellation, refund and privacy workflows have been tested.
- No public deployment or paid integrations without explicit owner approval.

## Offline editorial review history (development)
The `tools/editorial_workflow.py` module enforces state transitions:
`draft → fact_check → rights_review → approved → published`.
A reviewer can reject a record, return it to draft, or reopen a published
record for rights review. Each decision requires a reviewer, explanation,
and timezone-aware ISO timestamp. The append-only history is stored in
`internal_review_history` on the private record and is excluded from
`public-catalogue.json` by the exporter.

Approval and publication both re-run the publication validator. An
approval is not evidence that the underlying extraordinary claim is true.
Review decisions are offline operations; there is no public submission
or account-management interface yet. No records are published merely
by adding a review history. Keep private source files outside any
publicly served website directory.

## Explicit public export safeguard
The public catalogue export CLI now requires a separate publication manifest
(`world-wonder-publication-manifest-v1`) containing `source_sha256` and
`publish_ids`. The digest binds the approval to the exact canonical JSON
of the private source records, and the ID list must match all records marked
`published`. This prevents a stale or unexpectedly expanded source file
from silently changing the exported catalogue. Keep the manifest private,
review it independently, and never treat a manifest as a cryptographic
signature or proof of reviewer identity. The existing public website is not
affected until an explicitly reviewed export is supplied.
