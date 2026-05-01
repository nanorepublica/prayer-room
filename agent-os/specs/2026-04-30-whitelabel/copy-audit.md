# Whitelabel — Copy & Brand Audit

> Research note feeding into the eventual whitelabel spec. Goal: enumerate every
> hard-coded user-visible string in the app so we can decide what's
> *brand-identifying* (Phase 1) vs *everything else* (Phase 2 / out of scope).

## Recommendations at a glance

- **Phase 1 (brand-identifying + "Prayer" mentions):** the strings tagged
  `[BRAND]` below. These are the things a new operator will *immediately* want
  to change to make the app feel like theirs (brand name, hero copy, primary
  CTAs, footer) **plus every user-visible string that contains the literal word
  "Prayer"**, since those bake the original product name into otherwise generic
  copy.
- **Phase 2 candidates (operational copy):** strings tagged `[COPY]` — form
  helper text, success/error messages, empty states, confirmation dialog text
  that don't mention "Prayer". Useful to make editable but not required to ship
  a whitelabeled instance.
- **Out of scope (terminology):** `[TERM]` strings — words like "Praise",
  "Pray", "prayed", "Moderation", "Flagged". Changing these means rebranding
  the *concept* of the app and touches model field choices, URL names, etc.
  Best left as a separate, larger effort.
- **Out of scope (staff UI):** the staff/moderation UI is internal — operators
  will brand the *public* side. Strings listed for completeness only.

---

## Phase 1: editable strings `[BRAND]`

All strings that should be operator-editable in Phase 1. Mix of "brand identity"
items and operational copy that contains the word "Prayer".

### Brand identity strings (originally Phase 1)

| # | Where | Current text | Proposed key |
|---|---|---|---|
| 1 | `public_base.html` header logo, footer, `<title>` | "Prayer Room" | `brand.name` |
| 2 | `landing.html` H1 | "Welcome to the Prayer Room" *(currently uses `content.title` from `HomePageContent` with this fallback)* | `landing.title` |
| 3 | `landing.html` subtitle | "A place to share, pray, and encourage one another." *(also a `HomePageContent` fallback)* | `landing.subtitle` |
| 4 | `landing.html` primary CTA | "Submit a Prayer" | `cta.submit` |
| 5 | `landing.html` secondary CTA | "View Prayer Wall" | `cta.view_wall` |
| 6 | `wall.html` page title (`<title>`) | "Prayer Wall — Prayer Room" | composed from `brand.name` + `pages.wall.title` |
| 7 | `wall.html` H1 | "Prayer Wall" | `pages.wall.title` |
| 8 | `submit.html` H1 | "Submit a Prayer" | `pages.submit.title` |
| 9 | `submit.html` subtitle | "Your prayer will be reviewed before appearing on the wall." | `pages.submit.subtitle` |
| 10 | `_submit_success.html` heading | "Thank you" | `submit_success.title` |
| 11 | `_submit_success.html` body | "Your prayer has been submitted and will appear on the wall after review." | `submit_success.body` |
| 12 | `resources.html` H1 + `<title>` | "Prayer Resources" | `pages.resources.title` |
| 13 | `landing.html` cite block (the 4 `HomePageContent` keys already in DB) | `card_title`, `card_subtitle`, `card_description`, `card_link` | already DB-driven, just confirm they should be in scope |

### Pulled into Phase 1 — copy containing "Prayer"

| # | Where | Current text | Proposed key |
|---|---|---|---|
| 14 | `public_base.html` nav link | "Prayer Wall" | `nav.wall` *(reuse `pages.wall.title`?)* |
| 15 | `_prayer_card.html` type badge | "Prayer" | `badge.prayer` |
| 16 | `_prayer_card.html` flag aria-label | "Report this prayer" | `aria.report_prayer` |
| 17 | `_prayer_card.html` flag confirmation | `hx-confirm="Are you sure you want to report this prayer?"` | `confirm.report_prayer` |
| 18 | `_prayer_list.html` empty state | "No prayers yet." | `empty.wall_heading` |
| 19 | `submit.html` content field label | "Your Prayer or Praise" | `submit.content_label` |
| 20 | `forms.py` content placeholder | "Share your prayer or praise..." | `submit.content_placeholder` |

Notes:
- Items 13, 2, and 3 are *already* configurable via the existing
  `HomePageContent` model — landing.html falls back to hardcoded defaults when
  no DB row exists. Phase 1 should reuse / extend this pattern, not invent a
  new one.
- Item 17 (`hx-confirm`) is just an HTML attribute — easy to template.
- Items 16 and 17 are the only places `prayer` appears in lower-case/anchor
  text rather than as the product name.

---

## Phase 2 candidates: operational copy `[COPY]`

Useful to make editable, but not blocking a whitelabel launch. None of these
contain "Prayer".

### Public surface

| Where | Current text |
|---|---|
| `public_base.html` | Nav: "Resources", "Staff" |
| `_prayer_card.html` | Type badge: "Praise" *(also `[TERM]` — see below)* |
| `_prayer_card.html` | "I prayed for this" aria-label *(`[TERM]`)* |
| `_prayer_card.html` | Response label: "Response" |
| `_prayer_list.html` | "Be the first to submit one." |
| `_prayer_list.html` | "Load more" |
| `_submit_success.html` | "Submit Another" |
| `submit.html` | Field labels: "Type", "Name", "Location" |
| `submit.html` | Helper: "Leave blank to post anonymously." |
| `submit.html` | Submit button: "Submit" |
| `forms.py` | Placeholder: "Your name (optional)" |
| `wall.html` | Filter pill: "All" |
| `wall.html` | aria-label: "Filter by location" |
| `resources.html` | Empty: "No resources available yet." |

### Strings hardcoded in **Python**, not templates (need refactoring to make editable)

| Where | Current text |
|---|---|
| `public_views.py:91` | `FlagPrayerView` returns inline HTML: "Thank you for letting us know." |
| `models.py:37` | `name = models.TextField(default="Anon")` — default name when user posts anonymously |

The `FlagPrayerView` response is the most awkward — it's literal HTML inside a
view, doesn't even live in a template. If we want it editable, the view should
`render()` a tiny partial.

---

## Out of scope: terminology `[TERM]`

Strings that *are* the product, not its branding. Changing these means
rebuilding the app for a different domain. Touches model `choices=`, URL
names, admin verbose names, email templates.

- "Praise" — `PrayerType` enum, badge label, form legend
- "Pray" / "prayed" — button labels, prayer count, "I prayed for this"
  aria-label
- "Wall" (the *concept*, not the page title which is in Phase 1)
- "Flag" / "Report" — moderation concept (the verb)
- "Moderator", "Moderation" — staff role
- All `prayer-*` URL names

Recommendation: leave for a future "rebrandable" phase. Phase 1 assumes the new
operator is also running a prayer wall.

---

## Out of scope: staff/admin UI

Internal users will see this. Operators almost never want to brand it
differently from defaults. For completeness, the strings are:

- `base.html` site title: "Prayer Room"
- Nav: "Dashboard", "Moderation", "Flagged", "Respond", "Banned Words", "Email Templates", "Resources"
- `dashboard.html`: "Staff overview", "Dashboard — at a glance", "Needs attention", "Prayer wall activity", "Lifetime", "On the wall", "Approved (all time)", "Archived"
- `moderation.html` H1: "Moderation"
- `flagged.html` H1: "Flagged Requests"
- `prayer_response.html` H1: "Prayer Response"
- Plus tile labels populated from the view in `views.py`

Recommendation: leave hardcoded. If an operator does want to change them, they
can patch the templates — they're already in their fork.

---

## Strings already DB-driven today (no change needed)

For reference — these are *not* hardcoded and don't need to enter Phase 1:

- `HomePageContent` keys (`card_title`, `card_subtitle`, `card_description`,
  `card_link`, `page_subtitle`) — landing page card
- `PrayerInspiration` (verse + content) — landing page quote block
- `EmailTemplate` (subject + body) — all 3 notification email types
- `Setting.button_text` — feature toggle button labels
- `Location.name` — location filter pills
- `PrayerResource.title/description/content` — resources page

Strong existing pattern. Phase 1 implementation should reuse it (probably a
`SiteContent` model that's the same shape as `HomePageContent`, or just rename
+ extend `HomePageContent`).

---

## Phase 1 implementation — implied work

If **Phase 1 = the 20 strings above**, the work is:

1. One key/value content model + admin UI (extend or rename `HomePageContent`)
2. One context processor exposing `{{ brand.name }}` and `{{ site.<key> }}` to
   every template
3. Replace the 20 hard-coded strings with `{{ ... |default:"..." }}` lookups
4. Move the inline HTML in `FlagPrayerView` to a template so item 17's *response*
   message is editable (currently `public_views.py:91` is hardcoded — and is
   the response the user sees *after* confirming, so worth pulling in)
5. Seed the keys with current strings as defaults so nothing changes visually
   on a fresh install

Plus the **theming work** (Google Font + brand colour via env vars + CSS
variables, per the earlier conversation) — separate workstream.
