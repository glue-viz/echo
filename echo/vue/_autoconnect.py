import os
import warnings
from html.parser import HTMLParser

from ._connect import (connect_bool,
                       connect_value,
                       connect_text,
                       connect_choice)

__all__ = ['autoconnect_callbacks_to_vue', 'HANDLERS', 'TAG_TYPE_MAP']

HANDLERS = {
    'bool': connect_bool,
    'value': connect_value,
    'text': connect_text,
    'combosel': connect_choice,
}

TAG_TYPE_MAP = {
    'v-switch': 'bool',
    'v-checkbox': 'bool',
    'v-text-field': 'text',
    'v-slider': 'value',
    'v-range-slider': 'value',
    'v-select': 'combosel',
    'v-combobox': 'combosel',
    'v-autocomplete': 'combosel',
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
                # For v-text-field with type="number", use valuetext
                if inferred == 'text' and attrs_dict.get('type') == 'number':
                    echo_type = 'value'
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
                                 only=None):
    """
    Connect callback properties on ``instance`` to traitlets on
    ``widget`` bidirectionally, based on the Vue template.

    The connection type is inferred from the Vue tag name:

    * ``v-switch``, ``v-checkbox`` -- ``bool``
    * ``v-text-field`` -- ``text`` (or ``value`` when ``type="number"``)
    * ``v-slider``, ``v-range-slider`` -- ``value``
    * ``v-select``, ``v-combobox``, ``v-autocomplete`` -- ``combosel``

    For tags not in the default mapping (e.g. custom components), add an
    ``echo-type`` attribute to specify the connection type::

        <glue-float-field :value.sync="x_min" echo-type="value" />

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
    extras : dict, optional
        Additional properties to connect that are not discovered from
        the template (e.g. properties only referenced in ``v-if`` or
        JavaScript). Values can be:

        * A type string: ``'bool'``, ``'value'``, ``'text'``, or
          ``'combosel'``.
        * A tuple of ``(type, to_widget, from_widget)`` to supply
          custom transforms. ``to_widget`` converts the state value
          before setting the traitlet; ``from_widget`` converts the
          traitlet value before setting the state property.

    only : dict, optional
        When provided, skip template parsing and connect *only* the
        listed properties. Same value format as ``extras``. Useful
        for connecting properties from a secondary state object
        without re-parsing the template.

    Returns
    -------
    dict
        Mapping of property names to connection handler objects.
    """
    if only is not None:
        refs, transforms = _parse_extras(only)
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
            for wtype, prop_names in extra_refs.items():
                refs.setdefault(wtype, set()).update(prop_names)

    connections = {}

    for wtype, prop_names in refs.items():
        handler_cls = HANDLERS[wtype]
        for prop_name in prop_names:
            if not instance.is_callback_property(prop_name):
                warnings.warn(
                    f"Vue template references '{prop_name}' (type={wtype}) "
                    f"but '{prop_name}' is not a callback property on "
                    f"{type(instance).__name__}",
                    stacklevel=2,
                )
                continue
            to_w, from_w = transforms.get(prop_name, (None, None))
            handler = handler_cls(instance, prop_name, widget,
                                  to_widget=to_w, from_widget=from_w)
            connections[prop_name] = handler

    return connections
