from rest_framework.response import Response
from rest_framework.decorators import action
from minutes.models import Vertical, Edition
from minutes.api.common.serializers import (
    VerticalEditionsSerializer,
    EditionLiveSerializer,
    MinuteSummarySerializer,
    VerticalSerializer
)
from minutes.api.common.viewsets import BaseApiReadOnlyViewset


class VerticalViewset(BaseApiReadOnlyViewset):
    queryset = Vertical.objects.all()
    serializer_class = VerticalEditionsSerializer
    lookup_field = "slug"

    @action(detail=True, methods=["get"])
    def live(self, request, slug=None, pk=None):
        vertical = self.get_object()
        edition = Edition.objects.latest_live(vertical.id)

        return Response(
            EditionLiveSerializer(edition).data
        )

    @action(detail=True, methods=["get"])
    def archive(self, request, slug=None, pk=None):
        vertical = self.get_object()
        editions = Edition.objects.filter(vertical=vertical.id)
        minutes = [minute for edition in editions for minute in edition.minutes.all()]
        readyMinutes = [minute for minute in minutes if minute.ready_to_publish]
        readyMinutes.sort(reverse=True, key = lambda i: i.last_published)

        return Response(
            MinuteSummarySerializer(readyMinutes, many=True).data
        )

    @action(detail=True, methods=["get"])
    def lite(self, request, slug=None, pk=None):
        vertical = self.get_object()

        return Response(
            VerticalSerializer(vertical).data
        )
