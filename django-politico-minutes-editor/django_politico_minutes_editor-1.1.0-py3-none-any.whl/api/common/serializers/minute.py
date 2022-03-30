from minutes.models import Minute
from rest_framework import serializers


class MinuteSerializer(serializers.ModelSerializer):
    model = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    context = serializers.SerializerMethodField()

    def get_model(self, obj):
        return "Minute"

    def get_type(self, obj):
        return obj.type.name

    def get_context(self, obj):
        return obj.type.context

    class Meta:
        model = Minute
        fields = (
            "model",
            "slug",
            "handle",
            "id",
            "type",
            "ready_to_publish",
            "last_published",
            "content",
            "context",
        )

class MinuteSummarySerializer(serializers.ModelSerializer):
    headline = serializers.SerializerMethodField()
    edition = serializers.SerializerMethodField()

    def get_headline(self, obj):
        return obj.content.get("cover", {}).get("headline", "")

    def get_edition(self, obj):
        return obj.edition.published_datetime_slug()

    class Meta:
        model = Minute
        fields = (
            "slug",
            "edition",
            "handle",
            "id",
            "headline",
            "ready_to_publish",
            "last_published",
        )
