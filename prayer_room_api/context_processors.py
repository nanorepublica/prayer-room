def site_content(request):
    """
    Expose admin-editable site config to all templates as `{{ site.<key> }}`.

    Covers both brand identity (e.g. `site.brand_name`, `site.brand_primary_rgb`)
    and user-visible copy (e.g. `site.landing_title`). All keys live in the
    `SiteContent` table and are editable from the Django admin.

    Templates should always pair the lookup with `|default:"..."` so a missing
    key falls back to the original hardcoded text. This makes the migration
    safe even before data seeding runs.
    """
    from .models import SiteContent

    return {"site": dict(SiteContent.objects.values_list("key", "value"))}
