import logging

from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import PrayerPraiseRequest

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=PrayerPraiseRequest)
def check_response_change(sender, instance, **kwargs):
    """
    Trigger immediate notification when response_comment is added/changed.
    Only triggers when response_comment changes from empty to populated.
    """
    if not instance.pk:
        return  # New instance, no previous value

    try:
        old_instance = PrayerPraiseRequest.objects.get(pk=instance.pk)
    except PrayerPraiseRequest.DoesNotExist:
        return

    if not old_instance.response_comment and instance.response_comment:
        from .tasks import send_response_notification

        prayer_request_id = instance.pk
        transaction.on_commit(lambda: send_response_notification(prayer_request_id))
        logger.info(f"Queued response notification for prayer request {instance.pk}")
