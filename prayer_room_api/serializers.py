from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    Location,
    PrayerInspiration,
    PrayerPraiseRequest,
    PrayerResource,
    Setting,
    SiteContent,
    UserProfile,
)


class PrayerInspirationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PrayerInspiration
        fields = (
            "verse",
            "content",
        )


class SiteContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = SiteContent
        fields = (
            "key",
            "value",
        )


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("name", "slug", "id")


class PrayerPraiseRequestSerializer(serializers.ModelSerializer):
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())
    location_name = serializers.SlugRelatedField(
        source="location", slug_field="name", read_only=True
    )
    is_flagged = serializers.SerializerMethodField()
    is_archived = serializers.SerializerMethodField()
    is_approved = serializers.SerializerMethodField()
    prayer_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = PrayerPraiseRequest
        fields = (
            "id",
            "type",
            "name",
            "content",
            "response_comment",
            "prayer_count",
            "location",
            "location_name",
            "is_flagged",
            "is_archived",
            "is_approved",
            "created_at",
            "flagged_at",
            "archived_at",
            "approved_at",
        )

    def get_is_flagged(self, obj):
        return bool(obj.flagged_at)

    def get_is_archived(self, obj):
        return bool(obj.archived_at)

    def create(self, validated_data):
        user = None
        request = self.context.get("request")
        if request:
            user_data = request.data.get("user") or {}
            username = user_data.get("username")
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                if username:
                    # If user does not exist, create a new user
                    email = request.data.get("user", {}).get("email", "")
                    first_name = request.data.get("user", {}).get("name", "")
                    user = User.objects.create_user(
                        username, email, None, first_name=first_name
                    )
            validated_data["created_by"] = user
        instance = super().create(validated_data)
        instance.apply_banned_word_actions()
        instance.save()
        return instance

    def get_is_approved(self, obj):
        return bool(obj.approved_at)


class SettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ("name", "is_enabled", "button_text")


class PrayerResourceSerializer(serializers.ModelSerializer):
    section_name = serializers.SerializerMethodField()

    class Meta:
        model = PrayerResource
        fields = (
            "id",
            "title",
            "description",
            "resource_type",
            "section",
            "section_name",
            "url",
            "content",
            "sort_order",
            "created_at",
            "updated_at",
        )

    def get_section_name(self, obj):
        return obj.section.title if obj.section else None


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "user",
            "enable_digest_notifications",
            "enable_response_notifications",
        ]
