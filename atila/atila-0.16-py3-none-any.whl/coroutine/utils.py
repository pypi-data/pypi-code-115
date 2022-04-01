from ..events import *

WAS_FACTORY = None

def get_cloned_was (was_id):
    global WAS_FACTORY

    assert was_id, 'was.ID should be non-zero'
    if WAS_FACTORY is None:
        import skitai
        WAS_FACTORY = skitai.was

    _was = WAS_FACTORY._get_by_id (was_id)
    assert hasattr (_was, 'app'), 'Task future is available on only Atila'

    if isinstance (was_id, int): # origin
        return _was._clone ()
    return _was

def request_postprocessing (was, exc_info = None):
    if not hasattr (was.request, "_hooks"):
        return

    content = None
    success, failed, teardown = was.request._hooks
    try:
        if exc_info is None:
            success and success (was)
            was.app.emit (EVT_REQ_SUCCESS, None)
        else:
            if failed:
                content = failed (was, exc_info)
            was.app.emit (EVT_REQ_FAILED, exc_info)
    finally:
        teardown and teardown (was)
        was.app.emit (EVT_REQ_TEARDOWN)

    if content:
        return [content]

