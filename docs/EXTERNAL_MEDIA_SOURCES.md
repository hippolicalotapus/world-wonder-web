# External audio and video source integration

Status: implementation specification; no external media ingested or republished.

## Supported source types
- YouTube: official video or playlist URL, creator/channel name, video title, publication date, language, duration when known, and optional start timestamp.
- Podcasts: episode permalink and, when available, canonical RSS feed URL, show name, episode title, creator, publication date, and language.
- Institution-hosted audio/video: stable canonical link and rights metadata.
- Transcripts: only links or short, attributed excerpts within applicable permissions. Do not scrape, copy or redistribute full transcripts without permission.

## Source record
Each external-media record should contain:
- `id`, `title`, `mediaType` (`youtube`, `podcast`, `institutional-video`, `institutional-audio`)
- `canonicalUrl`, `publisher`, `creator` if different, `publishedAt` if known
- `archiveEntryIds` (references to existing research entries), `topics`, `language`
- `evidenceRole` (`primary`, `secondary`, `commentary`, `entertainment`)
- `verificationStatus` (`proposed`, `reviewing`, `reviewed`, `rejected`)
- `claimsAndCaveats` (human-authored summary distinguishing evidence from interpretation)
- `embedAllowed` (explicitly checked), `rightsNotes`, `reviewedAt`, `reviewer` when reviewed.

## Discovery and editorial workflow
1. Find relevant creator channels, individual episodes, academic lectures, archives and primary footage.
2. Confirm the source is authentic and the URL resolves to the intended work.
3. Check the creator's credibility and whether the episode is reporting evidence, presenting opinion or entertainment.
4. Associate the episode with specific archive entries; do not treat popularity or views as proof.
5. Write an original synopsis, attribution, content notes where appropriate, and a date of editorial review.
6. Link to the canonical source. Embed only where the platform and rights holder allow it, with an external-link fallback.
7. Periodically check for removed videos, broken links, changed claims and corrections.

## Playback, privacy and cost
- Prefer privacy-enhanced YouTube embeds where available, and only load embedded players after a visitor opts to play.
- Never download, rehost, or monetize third-party media without permission. Ads and memberships on our site do not confer redistribution rights.
- Respect podcast hosting and RSS terms. Do not proxy audio files or automatically generate unlicensed transcript copies.
- No paid APIs, third-party crawling subscriptions, public deployments, or mass outreach without owner approval.

## Site-specific editorial checks
- **Orbis Arcanorum:** distinguish original manuscript or museum documentation from speculative interpretations.
- **World Wicked Web:** add sensitive-content notices, protect victims' privacy, and do not sensationalize violence.
- **World Wonder Web:** distinguish documented events from faith claims, anecdotes and unverified miracles.

## Implementation milestones
1. Create and validate structured external-media records, with regression tests.
2. Add a filterable Audio & Video section to archive entry pages, including source labels and outbound links.
3. Add accessible opt-in embeds and mobile-friendly episode cards.
4. Add curator review, link health checks, corrections and rights auditing.
5. Evaluate opt-in creator partnerships and authorized podcast feeds.

Do not mark any of these features as live until verified end to end.
