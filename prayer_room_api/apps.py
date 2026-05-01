from django.apps import AppConfig


class PrayerConfig(AppConfig):
    name = "prayer_room_api"
    verbose_name = "Prayer Room"

    def ready(self):
        import prayer_room_api.signals  # noqa: F401
