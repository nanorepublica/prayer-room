from django.core.management.base import BaseCommand

from prayer_room_api.tasks import send_user_digest


class Command(BaseCommand):
    help = "Send the daily or weekly user digest email."

    def add_arguments(self, parser):
        parser.add_argument(
            "--frequency",
            choices=["daily", "weekly"],
            default="daily",
            help="Which digest cadence to send. Defaults to daily.",
        )

    def handle(self, *args, **options):
        result = send_user_digest(options["frequency"])
        self.stdout.write(result or "")
