.. currentmodule:: echo.vue

Interfacing with ipyvuetify widgets
------------------------------------

Echo includes functions to connect callback properties to
`ipyvuetify <https://github.com/widgetti/ipyvuetify>`_ widget traitlets.
Each connection is atomic per-property: changing a traitlet on the widget
only syncs that single property to the state, avoiding stale-overwrite
issues that arise from syncing an entire state dict at once.

Traitlets use the naming convention ``{type}_{name}`` where ``type``
determines the connection handler and ``name`` matches a callback property.
The supported types mirror the :ref:`Qt helpers <qtapi>`:

* ``bool``: boolean property ↔ ``Bool`` traitlet
* ``value``: numeric property ↔ ``Float`` traitlet
* ``valuetext``: numeric property ↔ ``Unicode`` traitlet (displayed as text)
* ``text``: string property ↔ ``Unicode`` traitlet
* ``combosel``: ``SelectionCallbackProperty`` ↔ ``combosel_{name}_items`` (List) + ``combosel_{name}_selected`` (Int) traitlets

Manual connections
^^^^^^^^^^^^^^^^^^

You can connect individual properties manually::

    import traitlets
    from echo import CallbackProperty
    from echo.vue import connect_bool

    class MyState:
        active = CallbackProperty(False)

    class MyWidget(traitlets.HasTraits):
        bool_active = traitlets.Bool(False).tag(sync=True)

    state = MyState()
    widget = MyWidget()
    connection = connect_bool(state, 'active', widget, 'bool_active')

If you omit the traitlet name, the traitlet is created dynamically::

    widget = traitlets.HasTraits()
    connection = connect_bool(state, 'active', widget)
    # widget now has a 'bool_active' traitlet

Automatic connections
^^^^^^^^^^^^^^^^^^^^^

:func:`autoconnect_callbacks_to_vue` parses the Vue template to determine
which properties to connect and what handler type to use. The template uses
the ``{type}_{name}`` naming convention in its bindings::

    <v-switch v-model="bool_active" />
    <glue-float-field :value.sync="value_x_min" />
    <v-select :items="combosel_x_att_items" v-model="combosel_x_att_selected" />

Only properties referenced in the template are connected. A warning is
issued if the template references a name that doesn't match any callback
property on the state. The template can be passed explicitly, or it is
resolved automatically from the widget's ``template_file`` class attribute::

    from echo.vue import autoconnect_callbacks_to_vue

    handlers = autoconnect_callbacks_to_vue(state, widget)
