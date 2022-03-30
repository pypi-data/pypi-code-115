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
    background = serializers.SerializerMethodField()
    edition = serializers.SerializerMethodField()

    def get_headline(self, obj):
        return obj.content.get("cover", {}).get("headline", "")

    def get_edition(self, obj):
        return obj.edition.published_datetime_slug()

    def get_background(self, obj):
        return {
            "src": obj.content.get("cover", {}).get("src", ""),
            "x": obj.content.get("cover", {}).get("x", 50),
            "y": obj.content.get("cover", {}).get("y", 50),
            "alt": obj.content.get("cover", {}).get("alt", ""),
        }

    class Meta:
        model = Minute
        fields = (
            "slug",
            "edition",
            "handle",
            "background",
            "id",
            "headline",
            "ready_to_publish",
            "last_published",
        )
