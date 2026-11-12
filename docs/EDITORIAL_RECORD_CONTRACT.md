# Editorial record contract — development draft

This is a content specification, not a published catalogue or a claim that any account, payment or evidence system exists.

## Public record (v1)

Each entry must have a stable `id`, `title`, `collection`, `summary`, `claim_type`, `review_status`, and a `sources` array. Allowed claim types: `documented_event`, `first_person_testimony`, `belief_or_tradition`, `unverified_report`. Do not present testimony, belief or an unverified report as a documented finding.

Each source must have `title`, `url`, `publisher`, `accessed_on` (YYYY-MM-DD), `source_type` (`primary`, `secondary`, `testimony`), and `rights_status` (`link_only`, `licensed`, `public_domain`, `permission_pending`). URLs are references, not automatic authorization to reproduce images or text.

## Review states

`draft` → `fact_check` → `rights_review` → `approved` → `published`. Rejection can occur at any stage. Only `published` records may appear as verified public catalogue entries, and only if at least one source is present, every source is linkable, and all reproduced media have cleared rights. `approved` does not itself mean publicly visible.

Keep an internal change log recording reviewer, timestamp, changed fields and reason. Do not place private submitter contact details, sensitive testimony or restricted evidence in public JSON.

## Separation of access

Public metadata and external source links may be served statically after editorial approval. Restricted evidence and paid content must remain server-side behind verified authorization; client-side hiding is not access control. No payment, subscription or login capability is implied by this contract.

## Launch gates

Before importing any real article, check source authenticity, claims language, privacy, reproduction rights, and any takedown request process. The first catalogue milestone should use a small set of fully sourced, rights-cleared records rather than invented examples.
