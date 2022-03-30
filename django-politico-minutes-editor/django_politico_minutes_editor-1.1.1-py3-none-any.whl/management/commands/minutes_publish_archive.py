from django.core.management.base import BaseCommand
from minutes.tasks.publish import publish_archive_api
from minutes.models import Vertical


class Command(BaseCommand):
    help = "Publishes a vertical's archive data"

    def add_arguments(self, parser):
        parser.add_argument("vertical", nargs="*", type=str)

    def handle(self, *args, **options):
        vertical = (
            options["vertical"][0] if len(options["vertical"]) > 0 else None
        )

        if vertical is not None:
            publish_archive_api(str(Vertical.objects.get(id=vertical).id))
        else:
            print("No valid vertical id provided.".format(vertical))
