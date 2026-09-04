# Freshness check catalogue

| ID | Check | Deterministic evidence |
|---|---|---|
| FR-01 | Update-date presence | Time-sensitive content lacks publication/modification/validity signal |
| FR-02 | Published vs modified | Modified date predates published date |
| FR-03 | Offer/event expiry | Explicit validity date has passed while item is presented active |
| FR-04 | Price corroboration | Comparable first-party price observations disagree |
| FR-05 | Availability corroboration | Comparable first-party availability observations disagree |
| FR-06 | Sitemap corroboration | Sitemap date conflicts with page evidence and mismatch is independently supported |
| FR-07 | Structured/visible corroboration | Important structured value differs from visible value |
| FR-08 | Policy freshness | Explicit policy validity/effective dates contradict current presentation |
| FR-09 | Cross-page factual consistency | Same first-party fact has materially different values |
| FR-10 | Time-sensitive claim qualification | Current/latest/now-style claim lacks supporting currency evidence |

Do not treat an old sitemap, missing HTTP Last-Modified, missing date on evergreen content, or visual appearance as proof of staleness.
