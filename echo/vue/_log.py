import logging

logger = logging.getLogger('echo')

# Global flag: when True, new widgets are automatically instrumented
_comm_logging_enabled = False

# Maps widget id -> (original_send, original_set_state, widget)
_patched_widgets = {}


def _short_repr(obj, limit=120):
    """Short repr that truncates long strings."""
    s = repr(obj)
    if len(s) > limit:
        return s[:limit] + '...'
    return s


def enable_comm_logging():
    """
    Enable logging of comm messages (state updates) between Python and the
    browser frontend for all widgets connected via
    :func:`~echo.vue.autoconnect_callbacks_to_vue` after this call.

    Messages are emitted at ``DEBUG`` level on the ``echo`` logger.
    """
    global _comm_logging_enabled
    _comm_logging_enabled = True


def disable_comm_logging():
    """
    Disable comm logging. Widgets already instrumented are unpatched, and
    future widgets will not be instrumented.
    """
    global _comm_logging_enabled
    _comm_logging_enabled = False
    for widget_id in list(_patched_widgets):
        original_send, original_set_state, widget = _patched_widgets.pop(widget_id)
        widget._send = original_send
        widget.set_state = original_set_state


def _enable_comm_logging_if_requested(widget):
    """Patch a single widget if comm logging is enabled and not already patched."""
    if not _comm_logging_enabled:
        return
    widget_id = id(widget)
    if widget_id in _patched_widgets:
        return
    if not hasattr(widget, '_send') or not hasattr(widget, 'set_state'):
        return

    original_send = widget._send
    original_set_state = widget.set_state
    _patched_widgets[widget_id] = (original_send, original_set_state, widget)

    label = type(widget).__name__

    def _logged_send(msg, buffers=None):
        if msg.get('method') == 'update':
            state = msg.get('state', {})
            logger.debug('[PY->VUE] %s: %s', label, _short_repr(state))
        return original_send(msg, buffers=buffers)

    def _logged_set_state(sync_data):
        logger.debug('[VUE->PY] %s: %s', label, _short_repr(sync_data))
        return original_set_state(sync_data)

    widget._send = _logged_send
    widget.set_state = _logged_set_state
