import os
import warnings
from html.parser import HTMLParser

from .connect import (connect_bool,
                      connect_value,
                      connect_valuetext,
                      connect_text,
                      connect_choice)

__all__ = ['autoconnect_callbacks_to_vue', 'HANDLERS']

HANDLERS = {
    'bool': connect_bool,
    'value': connect_value,
    'valuetext': connect_valuetext,
    'text': connect_text,
    'combosel': connect_choice,
}

# Attribute names that bind a Vue template expression to a traitlet.
_BINDING_ATTRS = {'v-model', ':items', ':value.sync', 'v-model.number'}


class _TemplateParser(HTMLParser):
    """Parse a Vue template and collect traitlet references from binding attributes."""

    def __init__(self):
        super().__init__()
        self.refs = {}

    def handle_starttag(self, tag, attrs):
        for attr_name, attr_value in attrs:
            if attr_name not in _BINDING_ATTRS or attr_value is None:
                continue
            if '_' not in attr_value:
                continue
            wtype, wname = attr_value.split('_', 1)
            if wtype not in HANDLERS:
                continue
            # Normalize selection suffixes to base property name
            for suffix in ('_items', '_selected'):
                if wname.endswith(suffix):
                    wname = wname[:-len(suffix)]
                    break
            self.refs.setdefault(wtype, set()).add(wname)


def _parse_template(template):
    """
    Parse a Vue template string and return a dict mapping handler type
    codes to sets of property names referenced in the template.

    Template references use the convention ``{type}_{name}`` (e.g.
    ``bool_x_log``, ``combosel_x_att_selected``). Both ``_items`` and
    ``_selected`` suffixes are normalized to the base property name.
    """
    parser = _TemplateParser()
    parser.feed(template)
    return parser.refs


def _resolve_template(widget):
    """
    Resolve the Vue template string from a widget. Checks for a
    ``template_file`` class attribute (tuple of module path and filename)
    or a ``template`` traitlet with a ``.template`` string attribute.
    Returns None if no template can be found.
    """
    for klass in type(widget).__mro__:
        tf = klass.__dict__.get('template_file')
        if tf is not None:
            if isinstance(tf, tuple) and len(tf) == 2:
                module_file, vue_filename = tf
                vue_path = os.path.join(os.path.dirname(module_file), vue_filename)
                if os.path.isfile(vue_path):
                    with open(vue_path) as f:
                        return f.read()
            break

    template = getattr(widget, 'template', None)
    if template is not None and hasattr(template, 'template'):
        return template.template

    return None


def autoconnect_callbacks_to_vue(instance, widget, template=None):
    """
    Connect callback properties on ``instance`` to traitlets on
    ``widget`` bidirectionally, based on the Vue template.

    The Vue template is parsed for binding references using the naming
    convention ``{type}_{name}`` (e.g. ``bool_x_log``,
    ``combosel_x_att_selected``). The type prefix determines the handler
    and the traitlet type to create. Traitlets are created dynamically on
    the widget. Only properties referenced in the template are connected,
    and a warning is issued if a reference doesn't match any callback
    property on ``instance``.

    The supported type prefixes mirror
    :func:`~echo.qt.autoconnect.autoconnect_callbacks_to_qt`:

    * ``bool``: boolean property ↔ ``Bool`` traitlet
    * ``value``: numeric property ↔ ``Float`` traitlet
    * ``valuetext``: numeric property ↔ ``Unicode`` traitlet
    * ``text``: string property ↔ ``Unicode`` traitlet
    * ``combosel``: selection property ↔ ``_items`` (List) + ``_selected`` (Int)

    Parameters
    ----------
    instance : HasCallbackProperties
        The state object with callback properties.
    widget : HasTraits
        The ipyvuetify widget.
    template : str, optional
        The Vue template string. If not provided, the template is
        resolved from the widget's ``template_file`` class attribute or
        ``template`` traitlet.

    Returns
    -------
    dict
        Mapping of property names to connection handler objects.
    """
    if template is None:
        template = _resolve_template(widget)
    if template is None:
        raise ValueError(
            "No Vue template found. Pass template= explicitly or ensure "
            "the widget has a template_file class attribute or template traitlet."
        )

    refs = _parse_template(template)
    handlers = {}

    for wtype, prop_names in refs.items():
        handler_cls = HANDLERS[wtype]
        for prop_name in prop_names:
            if not instance.is_callback_property(prop_name):
                warnings.warn(
                    f"Vue template references '{wtype}_{prop_name}' but "
                    f"'{prop_name}' is not a callback property on "
                    f"{type(instance).__name__}",
                    stacklevel=2,
                )
                continue
            handler = handler_cls(instance, prop_name, widget)
            handlers[prop_name] = handler

    return handlers
