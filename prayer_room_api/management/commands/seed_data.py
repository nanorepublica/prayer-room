"""
Seed development/demo data for the prayer room app.

Idempotent for reference data (locations, inspirations, settings, home page
content, banned words, resources) — running it twice will not duplicate them.
Prayer requests are only generated when the table is empty, since they have
no natural key to deduplicate against.

Usage:
    .venv/bin/python manage.py seed_data
    .venv/bin/python manage.py seed_data --reset-prayers   # wipe + regenerate prayers
    .venv/bin/python manage.py seed_data --clear           # wipe seeded data, do not re-seed
"""

import csv
import random
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import now

from prayer_room_api.models import (
    BannedWord,
    SiteContent,
    Location,
    PrayerInspiration,
    PrayerPraiseRequest,
    PrayerResource,
    Setting,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


SAMPLE_NAMES = [
    "Sarah", "James", "Hannah", "David", "Ruth", "Michael", "Esther", "Daniel",
    "Rebecca", "John", "Mary", "Peter", "Anna", "Tom", "Lydia", "Mark",
    "Anon", "Anon", "Anon",  # weight toward anonymous submissions
]

SAMPLE_PRAYERS = [
    "Please pray for my upcoming job interview on Thursday — I've been out of work for three months and this opportunity means a lot.",
    "Praying for healing for my mother who has been diagnosed with cancer. Asking God for strength for the whole family.",
    "Please pray for our marriage. We've been struggling and I know God can restore what feels broken.",
    "Asking for prayers for my exams next week. I'm anxious and finding it hard to focus.",
    "Please pray for my son who is far from God right now. I know He has a plan but it's hard to wait.",
    "Pray for our church plant in the north of the city — that God would soften hearts and open doors.",
    "I'm grateful — my biopsy came back clear! Praising God for His kindness.",
    "My friend is in hospital after an accident. Please pray for full recovery.",
    "Asking for wisdom about a big decision at work. Pray I'd hear God clearly.",
    "Please pray for peace in my home. There's been a lot of tension lately.",
    "Praise report — my visa was approved! Thank you to everyone who prayed.",
    "Pray for the youth group as they head off on retreat this weekend.",
    "I've been battling depression for years. Please pray for breakthrough.",
    "My dad isn't a believer. Please pray that God would soften his heart.",
    "Pray for our finances. We're behind on rent and don't know where to turn.",
    "Thank God with me — three years sober today.",
    "Please pray for my daughter who is being bullied at school.",
    "Asking for prayer for our missionaries in West Africa — security situation is tense.",
    "Pray for me as I start chemo on Monday. Trusting God but scared.",
    "Please pray for our pastor and his family — they are exhausted.",
]

SAMPLE_RESPONSES = [
    "Praying for you right now. May the peace of Christ guard your heart and mind.",
    "Lifting you up. God is faithful — He sees you.",
    "Standing with you in this. May God grant you wisdom and strength.",
    "Praying. Trusting God for breakthrough on your behalf.",
]

BANNED_WORDS = [
    ("idiot", BannedWord.AutoActionChoices.flag),
    ("hate", BannedWord.AutoActionChoices.flag),
    ("kill", BannedWord.AutoActionChoices.archive),
    ("scam", BannedWord.AutoActionChoices.archive),
]

PRAYER_RESOURCES = [
    {
        "title": "Getting Started",
        "resource_type": PrayerResource.ResourceType.SECTION,
        "description": "New to prayer? Start here.",
        "children": [
            {
                "title": "How to Pray — A Short Guide",
                "resource_type": PrayerResource.ResourceType.TEXT,
                "content": "Prayer is simply talking with God. You don't need fancy words. Try the ACTS pattern: Adoration, Confession, Thanksgiving, Supplication.",
            },
            {
                "title": "The Lord's Prayer Explained",
                "resource_type": PrayerResource.ResourceType.LINK,
                "url": "https://www.example.com/lords-prayer",
            },
        ],
    },
    {
        "title": "Going Deeper",
        "resource_type": PrayerResource.ResourceType.SECTION,
        "description": "For when you want to grow your prayer life.",
        "children": [
            {
                "title": "Praying the Psalms",
                "resource_type": PrayerResource.ResourceType.AUDIO,
                "url": "https://www.example.com/psalms-podcast",
            },
        ],
    },
]


def seed_locations():
    """Locations are referenced by prayer requests — ensure the basics exist."""
    defaults = [
        ("Main", "main"),
        ("Online", "online"),
        ("North Campus", "north"),
    ]
    for name, slug in defaults:
        Location.objects.get_or_create(
            slug=slug, defaults={"name": name, "is_active": True}
        )


def seed_from_csv(filename, model, field_map):
    """Load rows from a CSV under data/ into a model.

    field_map: {csv_column: model_field}. The first mapped field is treated
    as the natural key for idempotency.
    """
    path = DATA_DIR / filename
    if not path.exists():
        return 0

    natural_key = next(iter(field_map.values()))
    created = 0
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            kwargs = {model_field: row[csv_col] for csv_col, model_field in field_map.items()}
            key_value = kwargs.pop(natural_key)
            _, was_created = model.objects.get_or_create(
                **{natural_key: key_value}, defaults=kwargs
            )
            if was_created:
                created += 1
    return created


def seed_settings():
    """The CSV stores is_enabled as 'True'/'False' strings — coerce it."""
    path = DATA_DIR / "Settings-Grid view.csv"
    if not path.exists():
        return 0
    created = 0
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            _, was_created = Setting.objects.get_or_create(
                name=row["name"],
                defaults={
                    "is_enabled": row["is_enabled"].strip().lower() == "true",
                    "button_text": row["button_text"],
                },
            )
            if was_created:
                created += 1
    return created


def seed_banned_words():
    for word, action in BANNED_WORDS:
        BannedWord.objects.get_or_create(
            word=word, defaults={"auto_action": action, "is_active": True}
        )


def seed_resources():
    for order, section in enumerate(PRAYER_RESOURCES):
        section_obj, _ = PrayerResource.objects.get_or_create(
            title=section["title"],
            resource_type=section["resource_type"],
            defaults={
                "description": section.get("description", ""),
                "sort_order": order * 10,
            },
        )
        for child_order, child in enumerate(section["children"]):
            PrayerResource.objects.get_or_create(
                title=child["title"],
                resource_type=child["resource_type"],
                defaults={
                    "section": section_obj,
                    "url": child.get("url", ""),
                    "content": child.get("content", ""),
                    "sort_order": order * 10 + child_order + 1,
                },
            )


# ---------------------------------------------------------------------------
# >>> USER CONTRIBUTION GOES HERE <<<
#
# This function decides what state each generated prayer request lands in
# (pending / approved / flagged / archived / responded) AND how its created_at
# is distributed across the last 30 days. The shape of this data is what
# makes the staff dashboard interesting — see views.py:206 (StaffDashboardView).
#
# The dashboard shows:
#   - Tile counts: pending, flagged, awaiting_response, new in last 24h
#   - 30-day chart: bars (submitted), line (approved), tickmarks (flagged)
#
# Constraints / context to consider:
#   - Be realistic: in a healthy moderation flow, MOST requests get approved,
#     a small fraction are flagged, and very few are archived outright.
#   - Pending should be a meaningful but small backlog (e.g. 5-15 items),
#     otherwise the moderation page is overwhelming.
#   - Of approved requests, some should already have a `response_comment`
#     (so "awaiting response" tile isn't 0 or huge).
#   - Created_at distribution: should there be a recent surge, a steady drip,
#     a weekend dip? This is what makes the chart look "alive".
#   - PrayerType: most are PRAYER, some are PRAISE.
#
# You're writing ~5-10 lines that decide, for a single new prayer with a
# random offset_days (0..29) into the past:
#   - which fields to set: approved_at, flagged_at, archived_at, response_comment
#   - the prayer type (prayer vs praise)
#
# Implement build_prayer_state() below. It receives a `created_at` datetime
# and a Random instance (for reproducibility), and should return a dict of
# fields to apply to the PrayerPraiseRequest before saving.
# ---------------------------------------------------------------------------
def build_prayer_state(created_at, rng):
    """Decide the state of a fake prayer request.

    Args:
        created_at: timezone-aware datetime when this prayer was 'submitted'.
        rng: a random.Random instance (use rng.random(), rng.choice(), etc.
             instead of the module-level random functions, for reproducibility).

    Returns:
        dict of fields to set on the PrayerPraiseRequest, e.g.:
            {
                "type": "prayer",
                "approved_at": <datetime or None>,
                "flagged_at": <datetime or None>,
                "archived_at": <datetime or None>,
                "response_comment": <str>,
            }
    """
    type_ = (
        PrayerPraiseRequest.PrayerType.PRAISE
        if rng.random() < 0.15
        else PrayerPraiseRequest.PrayerType.PRAYER
    )
    state = {
        "type": type_,
        "approved_at": None,
        "flagged_at": None,
        "archived_at": None,
        "response_comment": "",
    }
    current = now()

    # Clip any future-dated decision time back to "now" so a prayer created
    # 30 minutes ago can't be "approved" 12 hours in the future.
    def clip(dt):
        return min(dt, current)

    roll = rng.random()
    if roll < 0.10:
        # Pending: untouched by moderation.
        return state
    if roll < 0.15:
        # Flagged: caught by a moderator (or the auto-flagger).
        state["flagged_at"] = clip(created_at + timedelta(minutes=rng.randint(5, 240)))
        return state
    if roll < 0.20:
        # Archived (denied): never approved.
        state["archived_at"] = clip(created_at + timedelta(hours=rng.randint(1, 8)))
        return state

    # Approved (~80%): set approved_at, then 40% of those get a response.
    state["approved_at"] = clip(created_at + timedelta(hours=rng.randint(1, 12)))
    if rng.random() < 0.40:
        state["response_comment"] = rng.choice(SAMPLE_RESPONSES)
    return state


def seed_prayers(reset=False):
    if reset:
        PrayerPraiseRequest.objects.all().delete()
    elif PrayerPraiseRequest.objects.exists():
        return 0

    rng = random.Random(42)  # reproducible runs
    locations = list(Location.objects.filter(is_active=True))
    if not locations:
        return 0

    current = now()
    count = 80
    created = 0
    for _ in range(count):
        offset_days = rng.randint(0, 29)
        offset_seconds = rng.randint(0, 86_399)
        created_at = current - timedelta(days=offset_days, seconds=offset_seconds)

        state = build_prayer_state(created_at, rng)

        PrayerPraiseRequest.objects.create(
            name=rng.choice(SAMPLE_NAMES),
            content=rng.choice(SAMPLE_PRAYERS),
            location=rng.choice(locations),
            created_at=created_at,
            prayer_count=rng.randint(0, 25),
            **state,
        )
        created += 1
    return created


def clear_seeded_data(stdout, style):
    """Reverse of the seed.

    Deletes everything this command would have created, identified by natural
    keys where possible. Anything pre-existing with the same natural key
    (e.g. a Location with slug='main' that you set up by hand) WILL be
    removed — there is no marker on rows that says "I was seeded".

    Order matters because of FK constraints: prayer requests reference
    locations (CASCADE), and PrayerResource children reference parent
    sections (SET_NULL). We delete the dependent rows first.
    """
    counts = {}

    counts["prayer_requests"] = PrayerPraiseRequest.objects.all().delete()[0]
    counts["inspirations"] = PrayerInspiration.objects.all().delete()[0]
    counts["site_content"] = SiteContent.objects.all().delete()[0]
    counts["settings"] = Setting.objects.all().delete()[0]

    seeded_words = [w for w, _ in BANNED_WORDS]
    counts["banned_words"] = BannedWord.objects.filter(word__in=seeded_words).delete()[0]

    seeded_titles = {section["title"] for section in PRAYER_RESOURCES} | {
        child["title"]
        for section in PRAYER_RESOURCES
        for child in section["children"]
    }
    counts["resources"] = PrayerResource.objects.filter(title__in=seeded_titles).delete()[0]

    seeded_slugs = ["main", "online", "north"]
    counts["locations"] = Location.objects.filter(slug__in=seeded_slugs).delete()[0]

    summary = ", ".join(f"{k}: -{v}" for k, v in counts.items() if v)
    stdout.write(style.WARNING(f"Cleared seeded data ({summary or 'nothing to clear'})."))


class Command(BaseCommand):
    help = "Seed development/demo data for the prayer room app."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-prayers",
            action="store_true",
            help="Delete all existing prayer requests before generating new ones.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete all seeded data (locations, prayers, settings, etc.) and exit "
                 "without re-seeding. Destructive: removes rows matching seeded natural "
                 "keys even if you set them up by hand.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            clear_seeded_data(self.stdout, self.style)
            return

        self.stdout.write("Seeding reference data...")
        seed_locations()
        inspirations = seed_from_csv(
            "Prayer Inspiration-Grid view.csv",
            PrayerInspiration,
            {"verse": "verse", "content": "content"},
        )
        site_content = seed_from_csv(
            "Home Page Content-Grid view.csv",
            SiteContent,
            {"key": "key", "value": "value"},
        )
        settings_count = seed_settings()
        seed_banned_words()
        seed_resources()

        self.stdout.write(self.style.SUCCESS(
            f"  inspirations: +{inspirations}, site content: +{site_content}, settings: +{settings_count}"
        ))

        self.stdout.write("Seeding prayer requests...")
        created = seed_prayers(reset=options["reset_prayers"])
        if created:
            self.stdout.write(self.style.SUCCESS(f"  created {created} prayer requests"))
        else:
            self.stdout.write("  skipped (use --reset-prayers to regenerate)")

        self.stdout.write(self.style.SUCCESS("Done."))
