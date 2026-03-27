import os
import warnings
from html.parser import HTMLParser

from ..containers import ListCallbackProperty, DictCallbackProperty
from ..selection import SelectionCallbackProperty

from ._connect import (connect_bool,
                       connect_int,
                       connect_float,
                       connect_text,
                       connect_choice,
                       connect_list,
                       connect_dict,
                       connect_any)
from ._log import _enable_comm_logging_if_requested

__all__ = ['autoconnect_callbacks_to_vue', 'HANDLERS', 'TAG_TYPE_MAP']

HANDLERS = {
    'bool': connect_bool,
    'int': connect_int,
    'float': connect_float,
    'text': connect_text,
    'selection': connect_choice,
    'list': connect_list,
    'dict': connect_dict,
    'any': connect_any,
}

TAG_TYPE_MAP = {
    'v-switch': 'bool',
    'v-checkbox': 'bool',
    'v-text-field': 'text',
    'v-slider': 'float',
    'v-range-slider': 'float',
    'v-select': 'selection',
    'v-combobox': 'selection',
    'v-autocomplete': 'selection',
}

# Attribute names that bind a Vue template expression to a traitlet.
_BINDING_ATTRS = {'v-model', ':items', ':value.sync', 'v-model.number'}


class _TemplateParser(HTMLParser):
    """Parse a Vue template and collect traitlet references from binding attributes."""

    def __init__(self):
        super().__init__()
        self.refs = {}

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # Check for binding attributes on this tag
        bindings = {k: v for k, v in attrs if k in _BINDING_ATTRS and v is not None}
        if not bindings:
            return

        # Determine connection type: echo-type attribute overrides tag inference
        echo_type = attrs_dict.get('echo-type')
        if echo_type is None:
            inferred = TAG_TYPE_MAP.get(tag)
            if inferred is not None:
                # For v-text-field with type="number", use int
                if inferred == 'text' and attrs_dict.get('type') == 'number':
                    echo_type = 'int'
                else:
                    echo_type = inferred
            else:
                for attr_value in bindings.values():
                    warnings.warn(
                        f"Vue template has binding '{attr_value}' on unknown "
                        f"tag <{tag}> with no echo-type attribute — skipping. "
                        f"Add echo-type=\"...\" to specify the connection type.",
                        stacklevel=2,
                    )
                return

        if echo_type not in HANDLERS:
            warnings.warn(
                f"Unknown echo-type '{echo_type}' on <{tag}> — skipping. "
                f"Supported types: {', '.join(sorted(HANDLERS))}",
                stacklevel=2,
            )
            return

        for attr_value in bindings.values():
            prop_name = attr_value
            # Normalize selection suffixes to base property name
            for suffix in ('_items', '_selected'):
                if prop_name.endswith(suffix):
                    prop_name = prop_name[:-len(suffix)]
                    break
            self.refs.setdefault(echo_type, set()).add(prop_name)


def _parse_template(template):
    """
    Parse a Vue template string and return a dict mapping handler type
    codes to sets of property names referenced in the template.

    The connection type is inferred from the Vue tag (e.g. ``v-switch``
    maps to ``bool``). A custom ``echo-type`` attribute on the tag
    overrides the inferred type.
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


def _infer_type(instance, prop_name):
    """Infer the connection type from the callback property descriptor."""
    prop = getattr(type(instance), prop_name)
    if isinstance(prop, SelectionCallbackProperty):
        return 'selection'
    if isinstance(prop, ListCallbackProperty):
        return 'list'
    if isinstance(prop, DictCallbackProperty):
        return 'dict'
    return 'any'


def _discover_properties(instance):
    """Return a refs dict for all callback properties on instance."""
    refs = {}
    for name in dir(instance):
        if not name.startswith('_') and instance.is_callback_property(name):
            wtype = _infer_type(instance, name)
            refs.setdefault(wtype, set()).add(name)
    return refs


def _parse_extras(extras):
    """Parse an extras/only dict into refs and transforms."""
    refs = {}
    transforms = {}
    for prop_name, spec in extras.items():
        if isinstance(spec, tuple):
            wtype, to_widget, from_widget = spec
            transforms[prop_name] = (to_widget, from_widget)
        else:
            wtype = spec
        if wtype not in HANDLERS:
            warnings.warn(
                f"Unknown type '{wtype}' for extra property "
                f"'{prop_name}' — skipping. Supported types: "
                f"{', '.join(sorted(HANDLERS))}",
                stacklevel=2,
            )
            continue
        refs.setdefault(wtype, set()).add(prop_name)
    return refs, transforms


def autoconnect_callbacks_to_vue(instance, widget, template=None, extras=None,
                                 only=None, skip=None,
                                 infer_properties_from='vue'):
    """
    Connect callback properties on ``instance`` to traitlets on
    ``widget`` bidirectionally.

    Parameters
    ----------
    instance : HasCallbackProperties
        The state object with callback properties.
    widget : HasTraits
        The ipyvuetify widget.
    infer_properties_from : ``'vue'`` or ``'python'``
        How to discover which properties to connect:

        * ``'vue'`` (default): parse the Vue template to find
          ``v-model`` / ``:value.sync`` bindings and infer types from
          the Vue tags (e.g. ``v-switch`` → bool, ``v-slider`` →
          float). Use ``extras`` for properties the parser cannot
          discover.
        * ``'python'``: discover all callback properties on
          ``instance`` and infer types from the property descriptors
          (``ListCallbackProperty`` → list, ``DictCallbackProperty``
          → dict, ``SelectionCallbackProperty`` → selection,
          others → any).

    template : str, optional
        The Vue template string. Only used when
        ``infer_properties_from='vue'``. If not provided, the
        template is resolved from the widget's ``template_file``
        class attribute or ``template`` traitlet.
    extras : dict, optional
        Additional properties to connect that are not discovered
        automatically. Values can be:

        * A type string: ``'bool'``, ``'int'``, ``'float'``,
          ``'text'``, ``'selection'``, ``'list'``, ``'dict'``, or
          ``'any'``.
        * A tuple of ``(type, to_widget, from_widget)`` to supply
          custom transforms.

    only : set or dict, optional
        When provided, connect *only* the listed properties (skip
        automatic discovery). Can be a set of property names (types
        auto-inferred) or a dict with the same value format as
        ``extras``.
    skip : set, optional
        Property names to skip (no warning, no connection).

    Returns
    -------
    dict
        Mapping of property names to connection handler objects.
    """
    if only is not None:
        if isinstance(only, set):
            refs = {}
            transforms = {}
            for prop_name in only:
                wtype = _infer_type(instance, prop_name)
                refs.setdefault(wtype, set()).add(prop_name)
        else:
            refs, transforms = _parse_extras(only)
    elif infer_properties_from == 'python':
        refs = _discover_properties(instance)
        transforms = {}

        if extras:
            extra_refs, transforms = _parse_extras(extras)
            extra_props = {p for names in extra_refs.values() for p in names}
            for wtype in refs:
                refs[wtype] -= extra_props
            for wtype, prop_names in extra_refs.items():
                refs.setdefault(wtype, set()).update(prop_names)
    else:
        if template is None:
            template = _resolve_template(widget)
        if template is None:
            raise ValueError(
                "No Vue template found. Pass template= explicitly or "
                "ensure the widget has a template_file class attribute "
                "or template traitlet."
            )

        refs = _parse_template(template)
        transforms = {}

        if extras:
            extra_refs, transforms = _parse_extras(extras)
            # Extras override any template-discovered type for the same
            # property (e.g. a v-select bound to a non-selection property
            # that is handled via a text transform instead).
            extra_props = {p for names in extra_refs.values() for p in names}
            for wtype in refs:
                refs[wtype] -= extra_props
            for wtype, prop_names in extra_refs.items():
                refs.setdefault(wtype, set()).update(prop_names)

    if skip:
        for wtype in refs:
            refs[wtype] -= skip

    _enable_comm_logging_if_requested(widget)

    connections = {}

    # Create connections with initial_sync=False so traits are added
    # without the sync tag, avoiding per-trait comm messages.
    for wtype, prop_names in refs.items():
        handler_cls = HANDLERS[wtype]
        for prop_name in prop_names:
            if not instance.is_callback_property(prop_name):
                if widget.has_trait(prop_name):
                    continue
                warnings.warn(
                    f"Vue template references '{prop_name}' (type={wtype}) "
                    f"but '{prop_name}' is not a callback property on "
                    f"{type(instance).__name__}",
                    stacklevel=2,
                )
                continue
            to_w, from_w = transforms.get(prop_name, (None, None))
            handler = handler_cls(instance, prop_name, widget,
                                  to_widget=to_w, from_widget=from_w,
                                  initial_sync=False)
            connections[prop_name] = handler

    # Set the initial values, enable sync, and send all state in one
    # comm message rather than one per trait.
    sync_keys = set()
    for handler in connections.values():
        handler._from_state()
        handler.enable_widget_sync()
        sync_keys.update(handler._sync_trait_names())

    if hasattr(widget, 'send_state') and sync_keys:
        widget.send_state(key=sync_keys)

    return connections
