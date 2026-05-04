from django.core.management.base import BaseCommand

from prayer_room_api.tasks import send_moderator_digest


class Command(BaseCommand):
    help = "Send the hourly moderator digest email to staff users."

    def handle(self, *args, **options):
        result = send_moderator_digest()
        self.stdout.write(result or "")
