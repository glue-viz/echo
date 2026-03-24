.. currentmodule:: echo.vue

Interfacing with ipyvuetify widgets
------------------------------------

Echo can automatically connect callback properties to
`ipyvuetify <https://github.com/widgetti/ipyvuetify>`_ widgets. An
ipyvuetify widget is a Python class backed by a Vue template file that
describes the UI layout using Vuetify components. For example, a simple
widget might look like this:

.. code-block:: python

    import ipyvuetify as v
    import traitlets

    class MyWidget(v.VuetifyTemplate):
        template_file = (__file__, 'my_widget.vue')

with a corresponding Vue template ``my_widget.vue``:

.. code-block:: none

    <template>
      <v-card>
        <v-switch v-model="active" label="Active" />
        <v-slider :value.sync="x_min" label="X Min" />
        <v-select :items="x_att_items" v-model="x_att_selected" />
      </v-card>
    </template>

Normally, you would need to manually define traitlets on the widget class
for each ``v-model`` binding in the template, and then write code to keep
those traitlets in sync with your application state. Echo automates this
entirely with :func:`autoconnect_callbacks_to_vue`:

.. code-block:: python

    from echo import CallbackProperty, SelectionCallbackProperty
    from echo.vue import autoconnect_callbacks_to_vue

    class MyState:
        active = CallbackProperty(False)
        x_min = CallbackProperty(0.0)
        x_att = SelectionCallbackProperty()

    state = MyState()
    widget = MyWidget()
    connections = autoconnect_callbacks_to_vue(state, widget)

This parses the Vue template, creates the necessary traitlets on the widget
automatically, and sets up bidirectional connections between the callback
properties and the widget traitlets. Changes to the callback properties
are reflected in the widget, and user interactions in the widget are
propagated back to the callback properties.

The connection type is inferred from the Vue component tag:

* ``v-switch``, ``v-checkbox`` -- boolean property
* ``v-text-field`` -- string property (or integer when ``type="number"`` is set)
* ``v-slider``, ``v-range-slider`` -- float property
* ``v-select``, ``v-combobox``, ``v-autocomplete`` -- selection property

For custom components not in the default mapping, use the ``echo-type``
attribute to specify the connection type. The supported ``echo-type``
values are ``bool``, ``int``, ``float``, ``text``, and ``selection``::

    <glue-float-field :value.sync="x_min" echo-type="float" />

Only properties referenced in the template that match callback properties
on the state object are connected. A warning is issued if the template
references a name that does not correspond to a callback property.
