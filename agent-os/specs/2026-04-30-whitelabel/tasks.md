# Task Breakdown: Whitelabel — brand theming + editable copy

## Overview
Two parallel tracks — theming (env-driven) and copy (admin-driven) — plus a
small refactor (FlagPrayerView, PrayerSubmitForm) so all 20 audited strings
become reachable.

## Track A: Theming

### Task Group 1: Brand settings + context processor
- [ ] 1.1 Add `BRAND_NAME`, `BRAND_PRIMARY_COLOR`, `BRAND_ON_PRIMARY_COLOR`,
      `BRAND_FONT_FAMILY`, `BRAND_FONT_GOOGLE_URL` to `Settings` class in
      `prayer_room_api/settings.py`
- [ ] 1.2 Create `prayer_room_api/context_processors.py` with `brand(request)`
      function returning `{"brand": {...}}`
- [ ] 1.3 Wire `brand` into `TEMPLATES.OPTIONS.context_processors` in settings
- [ ] 1.4 Test: brand context processor returns dict with all 5 keys, values
      come from settings

### Task Group 2: CSS variable injection + Google font
- [ ] 2.1 Add `:root` CSS variable injection to `public_base.html` `<head>`,
      driven by `{{ brand.* }}`
- [ ] 2.2 Conditionally render Google Fonts `<link>` tags when
      `brand.font_url` is truthy
- [ ] 2.3 Mirror the `:root` injection inside `base.html` `<style>` block (so
      staff CTAs pick up the brand colour via `--btn-primary-bg` override)

### Task Group 3: Tailwind theme extension
- [ ] 3.1 Extend `theme.colors` in `tailwind.config.js` with `brand` and
      `on-brand` mapped to CSS variables
- [ ] 3.2 Extend `theme.fontFamily.sans` to prefer `var(--brand-font)` then
      fall back to system stack
- [ ] 3.3 Run `just dev` (or `tailwind` CLI) once locally to confirm the
      classes generate

### Task Group 4: CTA class swap
- [ ] 4.1 Replace primary CTA classes in `landing.html` (Submit a Prayer
      button)
- [ ] 4.2 Replace primary CTA classes in `wall.html` (top button + active
      filter pill)
- [ ] 4.3 Replace primary CTA classes in `submit.html` (Submit button)
- [ ] 4.4 Replace primary CTA classes in `_submit_success.html` (View Prayer
      Wall button)
- [ ] 4.5 Visual check: light mode + dark mode both look correct with default
      brand colour (stone-900-equivalent)

## Track B: Editable copy

### Task Group 5: Model rename + admin
- [ ] 5.1 Tests: `SiteContent.get("missing_key", default="x") == "x"`,
      `SiteContent.get(existing_key) == row.value`, regression test that
      `LandingView` still resolves the original 5 keys
- [ ] 5.2 Rename `HomePageContent` → `SiteContent` in `models.py`. Add
      `unique=True`, bump `max_length` to 100 on `key`. Add `SiteContent.get()`
      classmethod
- [ ] 5.3 Update import in `public_views.py:LandingView`
- [ ] 5.4 Generate migration with `just manage makemigrations` — should be
      `RenameModel` + `AlterField`
- [ ] 5.5 Add data migration that uses `get_or_create` to seed the 20 keys
      with their default text (does not overwrite existing rows)
- [ ] 5.6 Register `SiteContent` in `admin.py` with `list_display`,
      `search_fields`, `ordering`
- [ ] 5.7 Run migrations locally; confirm admin lists all 25 keys

### Task Group 6: SiteContent context processor
- [ ] 6.1 Add `site_content(request)` function to `context_processors.py`
- [ ] 6.2 Wire into `TEMPLATES.OPTIONS.context_processors`
- [ ] 6.3 Test: returns dict with all rows; missing keys absent (template
      `|default:` handles fallback)

### Task Group 7: Template string replacements
For each row in the 20-key table in `spec.md`, replace the hardcoded string
with `{{ site.<key>|default:"<current text>" }}`. One commit per template is
fine.

- [ ] 7.1 `public_base.html`: `brand_name` (header logo, footer, title),
      `nav_wall`, `nav_resources`
- [ ] 7.2 `landing.html`: already-templated `card_*` keys remain; add
      `landing_title`, `landing_subtitle`, `cta_submit`, `cta_view_wall`
      (note these have `content.X` fallback today via `HomePageContent`;
      switch them to `site.X` for consistency, or leave the existing keys —
      decide while implementing)
- [ ] 7.3 `wall.html`: `pages_wall_title`, `cta_submit` (top button)
- [ ] 7.4 `submit.html`: `pages_submit_title`, `pages_submit_subtitle`,
      `submit_content_label`
- [ ] 7.5 `_submit_success.html`: `submit_success_title`, `submit_success_body`,
      `cta_view_wall`
- [ ] 7.6 `resources.html`: `pages_resources_title`
- [ ] 7.7 `_prayer_card.html`: `badge_prayer`, `aria_report_prayer`,
      `confirm_report_prayer`
- [ ] 7.8 `_prayer_list.html`: `empty_wall_heading`

### Task Group 8: View + form refactor
- [ ] 8.1 Create `prayer_wall/_flag_thanks.html` partial using
      `{{ site.flag_thanks|default:"..." }}`
- [ ] 8.2 Update `FlagPrayerView.post()` in `public_views.py` to `render()`
      the new partial instead of returning inline HTML
- [ ] 8.3 Test: posting to flag URL returns the expected text (or a 200 with
      the rendered partial)
- [ ] 8.4 Move `PrayerSubmitForm` content placeholder from class `widgets` to
      `__init__`, reading from `SiteContent.get("submit_content_placeholder",
      default="...")`
- [ ] 8.5 Test: form renders with placeholder from DB if set, default
      otherwise

## Track C: Verification + docs

### Task Group 9: End-to-end checks
- [ ] 9.1 Run full test suite (`just manage test`)
- [ ] 9.2 Start dev server, browse:
      - landing page → header/footer say brand name, hero CTAs show brand colour
      - wall → submit button has brand colour, active filter pill has brand colour
      - submit → form submits, success message editable
      - flag a prayer → "Thank you for letting us know" appears
      - dark mode toggles correctly on all pages
      - Set `BRAND_NAME=Test`, `BRAND_PRIMARY_COLOR="220 38 38"` in `.env`,
        restart, confirm changes propagate
- [ ] 9.3 Edit a `SiteContent` row in admin, refresh public page, confirm
      change appears

### Task Group 10: Docs
- [ ] 10.1 Update `README.md` with whitelabel section: env vars, format
      requirements (rgb triplets), where to edit copy

## Implementation order
Recommended order: 1 → 2 → 3 → 5 → 6 → 7 → 8 → 4 → 9 → 10.

Reasoning: settings + context processors first (everything downstream depends
on them), then templates can reach for `{{ site.X }}` and `{{ brand.X }}`.
The CTA class swap (4) is left until after copy work because the CTAs are the
last thing visually obvious — easier to verify when the rest is in place.
