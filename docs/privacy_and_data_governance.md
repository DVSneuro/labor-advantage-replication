# Privacy and data-governance audit

The repository is public and the new pipeline is restricted to public, institution-
level federal statistical data, the public Zhang replication archive, and public
bibliographic metadata. No proprietary Academic Analytics/AARC individual-level data,
credentials, access tokens, or private human-subject records were found.

The legacy directory contains NIH RePORTER exports with public award and principal-
investigator names. Those names are public metadata rather than private research data,
but the manual export is not an input to the new reproducible pipeline. It is retained
only to preserve repository history and provenance.

Operational safeguards:

- Raw, interim, and processed data are ignored and regenerated from scripts.
- Downloaded raw files are immutable; changed bytes require an explicit intervention.
- The tracked download manifest records URLs, retrieval times, file sizes, checksums,
  licenses/access notes, and documentation.
- API credentials must be supplied through environment variables and must never be
  committed. OpenAlex uses `OPENALEX_API_KEY`; `OPENALEX_EMAIL` is optional contact
  metadata.
- Candidate fuzzy institution matches are review artifacts only. They never enter the
  panel automatically.
- Published person names in legacy NIH files should not be repurposed for person-level
  performance analysis without a separate governance review.

No repository-history rewrite is recommended: the tracked legacy files are public,
and rewriting would add collaboration risk without removing a private-data exposure.
