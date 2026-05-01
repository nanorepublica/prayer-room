# Specification: Whitelabel — brand theming + editable copy

## Goal
Allow operators of a self-hosted prayer-room instance to brand the public-facing
UI without code changes — by setting brand identity via env vars (deploy-time)
and editing user-visible copy via the Django admin (runtime).

Single-tenant: one deploy per brand. No multi-tenant runtime resolution.

## User Stories
- As an operator, I want to set a brand name, primary colour and Google font
  via env vars so the public UI matches my organisation
- As a staff admin, I want to edit user-visible site copy from the Django admin
  so I can adjust phrasing without redeploying
- As a visitor, I should see no behavioural change when no brand env vars are
  set and no `SiteContent` rows exist (current strings/colours remain the
  defaults)

## Scope

### In scope
- 20 user-visible strings made editable (full list in `copy-audit.md`,
  Phase 1 section). Mix of brand identity (e.g. "Prayer Room") and copy
  containing the literal word "Prayer".
- One brand colour (with derived "text-on-brand" colour for legibility)
- Google Font support via env vars
- Text logo only (the brand name string)
- Light + dark mode preserved as-is
- Public-facing surface only (`public_base.html`, `prayer_wall/*`)

### Out of scope
- Image logos
- Multi-tenant runtime / hostname-based brand resolution
- Staff/admin UI strings (internal users)
- Terminology like "Praise", "Pray", "prayed", "Moderation"
- Full colour palettes (secondary/accent/neutral)
- Forcing dark or light mode per brand

## Architecture decision: unified DB-backed config

All whitelabel configuration — both brand identity (name, colour, font) and
user-visible copy — lives in a single `SiteContent` key/value table edited
from the Django admin. **No env vars** for brand settings. Rationale:

- Multi-line copy strings are awkward in env files
- Project already follows this pattern (`HomePageContent`, `Setting`,
  `EmailTemplate`, `PrayerInspiration`)
- One mental model for operators: "go to the admin"
- Brand changes don't require a redeploy

Cost: one extra DB query per page render (one `SELECT` against ~25 rows).
Easily cached if it shows up in profiling.

## Technical Approach

### A. Theming track (DB-driven)

The 5 brand keys (stored as `SiteContent` rows):

| Key | Default value | Notes |
|---|---|---|
| `brand_name` | "Prayer Room" | Reused as the wordmark/title/footer |
| `brand_primary_rgb` | "23 23 23" | RGB triplet, space-separated, for Tailwind alpha modifiers |
| `brand_on_primary_rgb` | "255 255 255" | Text colour on brand backgrounds |
| `brand_font_family` | "" | e.g. "Inter". Empty = system stack |
| `brand_font_google_url` | "" | Empty = no Google font loaded |

The RGB-triplet format (rather than hex) is required so Tailwind utilities can
apply alpha modifiers like `bg-brand/40` via the `<alpha-value>` placeholder.

#### `public_base.html` head injection
```html
<style>
:root {
  --brand-primary: {{ site.brand_primary_rgb|default:"23 23 23" }};
  --brand-on-primary: {{ site.brand_on_primary_rgb|default:"255 255 255" }};
  {% if site.brand_font_family %}--brand-font: "{{ site.brand_font_family }}";{% endif %}
}
</style>
{% if site.brand_font_google_url %}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{{ site.brand_font_google_url }}">
{% endif %}
```

#### `base.html` (staff) integration
Same `:root` injection (the existing big `<style>` block). Override the
existing `--btn-primary-bg` to use the brand colour:
```css
:root {
  --btn-primary-bg: rgb(var(--brand-primary));
  --btn-primary-hover: rgb(var(--brand-primary) / 0.85);
}
```
This way staff CTAs pick up the brand colour for free, without touching every
template. Acceptable scope creep — implementation cost is ~3 lines.

#### `tailwind.config.js` extension
```js
theme: {
  extend: {
    colors: {
      brand: 'rgb(var(--brand-primary) / <alpha-value>)',
      'on-brand': 'rgb(var(--brand-on-primary) / <alpha-value>)',
    },
    fontFamily: {
      sans: ['var(--brand-font, ui-sans-serif)', 'system-ui', '-apple-system', 'sans-serif'],
    },
  },
}
```
Applying `font-sans` to body (or letting Tailwind's preflight do it) picks up
the brand font everywhere. If `--brand-font` is unset, falls back to system.

#### CTA class swap
Replace `bg-stone-900 dark:bg-stone-100 text-white dark:text-stone-900` with
`bg-brand text-on-brand` on:
- `landing.html` Submit a Prayer button
- `wall.html` Submit a Prayer button (top of wall)
- `submit.html` Submit button
- `_submit_success.html` View Prayer Wall button
- `wall.html` active filter pill (`bg-stone-900 ... border-stone-900` → `bg-brand text-on-brand border-brand`)

The brand colour stays the brand colour in dark mode (industry-standard
approach — Slack purple stays purple). Surrounding neutrals continue to
invert via `dark:` variants.

### B. Copy track (DB-driven)

#### Model rename: `HomePageContent` → `SiteContent`
Migration steps:
1. `RenameModel("HomePageContent", "SiteContent")`
2. `AlterField("key", max_length=100, unique=True)` (existing field is
   non-unique, max_length=50 — both need bumping)
3. Data migration: for each of the 24 keys (5 brand + 19 copy — `brand_name`
   moves from copy to brand), `get_or_create(key=..., defaults={"value":
   <default_text>})` — preserves any existing `HomePageContent` rows
   untouched, just adds new keys

#### Context processor `prayer_room_api.context_processors.site_content`
Returns:
```python
{"site": dict(SiteContent.objects.values_list("key", "value"))}
```
One query per request. Fast enough; can add caching later if it shows up in
profiling.

#### Template replacements
Pattern:
```django
{{ site.brand_name|default:"Prayer Room" }}
```
Defaults match current text so no visual change on a fresh install before the
data migration runs.

#### Model admin
Register `SiteContent` in `admin.py` with:
- `list_display = ["key", "value_preview"]`
- `search_fields = ["key", "value"]`
- `ordering = ["key"]`

The admin already handles the rest. No bespoke UI needed.

#### `FlagPrayerView` refactor
Current `public_views.py:91` returns inline HTML. Replace with:
```python
return render(request, "prayer_wall/_flag_thanks.html")
```
And create `_flag_thanks.html`:
```django
<p class="text-sm text-stone-500 dark:text-stone-400 italic">
  {{ site.flag_thanks|default:"Thank you for letting us know." }}
</p>
```

#### `PrayerSubmitForm` placeholder refactor
Current `forms.py:20-25` hardcodes the textarea placeholder at class-definition
time. Move to `__init__` so it's read at runtime:
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields["location"].queryset = Location.objects.filter(is_active=True)
    self.fields["name"].required = False
    self.fields["content"].widget.attrs["placeholder"] = SiteContent.get(
        "submit_content_placeholder",
        default="Share your prayer or praise...",
    )
```
Add a `SiteContent.get(key, default)` classmethod that wraps `objects.filter(...).values_list("value", flat=True).first()` with a default fallback.

(The `name` field placeholder doesn't contain "Prayer" so stays hardcoded per
the audit decision.)

### C. Key list — 24 SiteContent keys to seed

5 brand identity (above) plus 19 copy keys:

| Key | Default value |
|---|---|
| `landing_title` | "Welcome to the Prayer Room" |
| `landing_subtitle` | "A place to share, pray, and encourage one another." |
| `cta_submit` | "Submit a Prayer" |
| `cta_view_wall` | "View Prayer Wall" |
| `pages_wall_title` | "Prayer Wall" |
| `pages_submit_title` | "Submit a Prayer" |
| `pages_submit_subtitle` | "Your prayer will be reviewed before appearing on the wall." |
| `submit_success_title` | "Thank you" |
| `submit_success_body` | "Your prayer has been submitted and will appear on the wall after review." |
| `pages_resources_title` | "Prayer Resources" |
| `nav_wall` | "Prayer Wall" |
| `badge_prayer` | "Prayer" |
| `aria_report_prayer` | "Report this prayer" |
| `confirm_report_prayer` | "Are you sure you want to report this prayer?" |
| `empty_wall_heading` | "No prayers yet." |
| `submit_content_label` | "Your Prayer or Praise" |
| `submit_content_placeholder` | "Share your prayer or praise..." |
| `flag_thanks` | "Thank you for letting us know." |
| `nav_resources` | "Resources" |

Plus the 4 existing keys (`card_title`, `card_subtitle`, `card_description`,
`card_link`, `page_subtitle`) preserved untouched by the migration.

## Reusable Components

### Existing Code to Leverage
- `HomePageContent` model and its existing usage pattern in `LandingView`
- `Settings` class hierarchy in `settings.py` with `cbs` env helper
- Tailwind CLI integration (`django-tailwind-cli`)
- The CSS-variable system already in `base.html` for staff theming

### New Components
- `prayer_room_api/context_processors.py` (new file, two functions)
- `prayer_wall/_flag_thanks.html` partial
- New migrations for rename + seed
- `SiteContent.get()` classmethod helper

## Testing

- Test each context processor returns expected shape
- Test `SiteContent.get()` returns DB value, falls back to default when missing
- Test `LandingView` still resolves existing `HomePageContent` keys
  (regression — they remain accessible on the renamed model)
- Test the data migration is idempotent (forwards + backwards safe)
- No need to test individual template substitutions — they're trivial
  `{{ var|default }}` usage

## Configuration / Deploy notes
- All new env vars have safe defaults; existing deploys continue to work
  unchanged
- Operators wanting to rebrand:
  1. Set `BRAND_NAME`, `BRAND_PRIMARY_COLOR` (rgb triplet), `BRAND_ON_PRIMARY_COLOR`
     in their environment
  2. Optionally set `BRAND_FONT_FAMILY` and `BRAND_FONT_GOOGLE_URL`
  3. Edit `SiteContent` rows from the Django admin
- README update with the above

## Risks / Open questions
- **Tailwind class purging**: `bg-brand` and `text-on-brand` are referenced in
  templates so the existing `content: ["./templates/**/*.html"]` glob picks
  them up. No safelist needed.
- **CSP**: if a strict Content-Security-Policy is added later, the inline
  `<style>` block injecting `:root` vars will need to be moved to a static
  CSS file or the CSP needs a hash. Not currently in place.
- **`SiteContent.get()` queries per request**: form-init reads can hit the DB
  on every form render. Acceptable for the submit form (low traffic). If we
  later expose more form fields this way, batch via the context processor.
