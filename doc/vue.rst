.. currentmodule:: echo.vue

Interfacing with ipyvuetify widgets
------------------------------------

Echo includes functions to connect callback properties to
`ipyvuetify <https://github.com/widgetti/ipyvuetify>`_ widget traitlets.
Each connection is atomic per-property: changing a traitlet on the widget
only syncs that single property to the state, avoiding stale-overwrite
issues that arise from syncing an entire state dict at once.

The connection type is inferred from the Vue tag in the template:

* ``v-switch``, ``v-checkbox`` -- ``bool``: boolean property, ``Bool`` traitlet
* ``v-text-field`` -- ``text``: string property, ``Unicode`` traitlet (or ``valuetext`` when ``type="number"``)
* ``v-slider``, ``v-range-slider`` -- ``value``: numeric property, ``Float`` traitlet
* ``v-select``, ``v-combobox``, ``v-autocomplete`` -- ``combosel``: ``SelectionCallbackProperty``, ``{name}_items`` (List) + ``{name}_selected`` (Int) traitlets

For custom components not in the default mapping, use the ``echo-type``
attribute to specify the connection type::

    <glue-float-field :value.sync="x_min" echo-type="value" />

Manual connections
^^^^^^^^^^^^^^^^^^

You can connect individual properties manually. If you omit the traitlet
name, the traitlet is created dynamically using the property name::

    import traitlets
    from echo import CallbackProperty
    from echo.vue import connect_bool

    class MyState:
        active = CallbackProperty(False)

    state = MyState()
    widget = traitlets.HasTraits()
    connection = connect_bool(state, 'active', widget)
    # widget now has an 'active' Bool traitlet

If the widget already has a traitlet with a different name, pass it
explicitly::

    class MyWidget(traitlets.HasTraits):
        is_enabled = traitlets.Bool(False).tag(sync=True)

    widget = MyWidget()
    connection = connect_bool(state, 'active', widget, 'is_enabled')

Automatic connections
^^^^^^^^^^^^^^^^^^^^^

:func:`autoconnect_callbacks_to_vue` parses the Vue template to determine
which properties to connect. The tag determines the handler type and the
``v-model`` value is the property name directly::

    <v-switch v-model="active" />
    <v-slider :value.sync="x_min" />
    <v-select :items="x_att_items" v-model="x_att_selected" />

Only properties referenced in the template are connected. A warning is
issued if the template references a name that doesn't match any callback
property on the state. The template can be passed explicitly, or it is
resolved automatically from the widget's ``template_file`` class attribute::

    from echo.vue import autoconnect_callbacks_to_vue

    handlers = autoconnect_callbacks_to_vue(state, widget)
