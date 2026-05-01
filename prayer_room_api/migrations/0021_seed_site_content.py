from django.db import migrations


SEED_DATA = [
    # Brand identity
    ("brand_name", "Prayer Room"),
    ("brand_primary_rgb", "23 23 23"),
    ("brand_on_primary_rgb", "255 255 255"),
    ("brand_font_family", ""),
    ("brand_font_google_url", ""),
    # Landing page
    ("landing_title", "Welcome to the Prayer Room"),
    ("landing_subtitle", "A place to share, pray, and encourage one another."),
    # Calls to action (re-used across multiple pages)
    ("cta_submit", "Submit a Prayer"),
    ("cta_view_wall", "View Prayer Wall"),
    # Page titles + subtitles
    ("pages_wall_title", "Prayer Wall"),
    ("pages_submit_title", "Submit a Prayer"),
    (
        "pages_submit_subtitle",
        "Your prayer will be reviewed before appearing on the wall.",
    ),
    ("pages_resources_title", "Prayer Resources"),
    # Submit success screen
    ("submit_success_title", "Thank you"),
    (
        "submit_success_body",
        "Your prayer has been submitted and will appear on the wall after review.",
    ),
    # Submit form
    ("submit_content_label", "Your Prayer or Praise"),
    ("submit_content_placeholder", "Share your prayer or praise..."),
    # Navigation
    ("nav_wall", "Prayer Wall"),
    ("nav_resources", "Resources"),
    # Prayer card
    ("badge_prayer", "Prayer"),
    ("aria_report_prayer", "Report this prayer"),
    ("confirm_report_prayer", "Are you sure you want to report this prayer?"),
    # Empty / response states
    ("empty_wall_heading", "No prayers yet."),
    ("flag_thanks", "Thank you for letting us know."),
]


def seed_site_content(apps, schema_editor):
    SiteContent = apps.get_model("prayer_room_api", "SiteContent")
    for key, value in SEED_DATA:
        SiteContent.objects.get_or_create(key=key, defaults={"value": value})


def remove_seeded_site_content(apps, schema_editor):
    SiteContent = apps.get_model("prayer_room_api", "SiteContent")
    SiteContent.objects.filter(key__in=[key for key, _ in SEED_DATA]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("prayer_room_api", "0020_rename_homepagecontent_to_sitecontent"),
    ]

    operations = [
        migrations.RunPython(seed_site_content, remove_seeded_site_content),
    ]
