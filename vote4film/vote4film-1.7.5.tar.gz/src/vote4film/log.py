import logging
import uuid


class ContextFilter(logging.Filter):
    """Add contextual information to all logs:

    Adds:
        - A random request UUID for each individual request (record.request_uuid)

    NB: Relies on this app effectively being single-threaded.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uuid = None
        self.user_pk = None

    def __call__(self):
        # When logging constructs this filter, return the global instance.
        return global_context_filter

    def start_request(self, request):
        self.uuid = uuid.uuid4()
        if request:
            request.uuid = self.uuid

    def update_user_info(self, request):
        # Called by middleware (in a different place in the order)
        if request.user and request.user.is_authenticated:
            self.user_pk = request.user.pk

    def end_request(self):
        self.uuid = None
        self.user_pk = None

    def filter(self, record):
        record.request_uuid = self.uuid
        record.request_user = self.user_pk
        return True


global_context_filter = ContextFilter()
