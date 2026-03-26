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
attribute to specify the connection type::

    <glue-float-field :value.sync="x_min" echo-type="float" />

The supported ``echo-type`` values are: ``bool``, ``int``, ``float``,
``text``, ``selection``, ``list``, ``dict``, and ``any``.

Only properties referenced in the template that match callback properties
on the state object are connected. A warning is issued if the template
references a name that does not correspond to a callback property.

Connecting list and dict properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``ListCallbackProperty`` and ``DictCallbackProperty`` can be connected
to Vue using the ``list`` and ``dict`` types. These are typically
specified via the ``extras`` parameter since list/dict bindings are
not automatically inferred from standard Vuetify tags:

.. code-block:: python

    from echo import ListCallbackProperty, DictCallbackProperty

    class AppState:
        items = ListCallbackProperty([{'name': 'a'}])
        settings = DictCallbackProperty({'visible': True})

    state = AppState()
    widget = MyWidget()
    autoconnect_callbacks_to_vue(state, widget,
                                 extras={'items': 'list', 'settings': 'dict'})

Mutations to the containers (e.g. ``state.items.append(...)`` or
``state.settings['visible'] = False``) are synced to the widget.
Each mutation triggers a full sync of the container, so use
``delay_callback`` to batch several mutations into a single sync.
In the reverse direction (widget → state), the existing
``CallbackList`` / ``CallbackDict`` objects are updated in place so
that any attached callbacks are preserved.

Discovering properties from Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, ``autoconnect_callbacks_to_vue`` discovers which
properties to connect by parsing the Vue template. For state objects
whose properties may not all appear in the template (e.g. an
application-level state used across many components), you can instead
discover properties directly from the Python class:

.. code-block:: python

    autoconnect_callbacks_to_vue(state, widget,
                                 infer_properties_from='python')

This discovers all ``CallbackProperty`` attributes on the state
object and infers the connection type from the property descriptor:

* ``ListCallbackProperty`` → ``list``
* ``DictCallbackProperty`` → ``dict``
* ``SelectionCallbackProperty`` → ``selection``
* All other ``CallbackProperty`` → ``any`` (uses ``traitlets.Any``,
  no type coercion)

You can still use ``extras`` to override specific properties with
custom transforms, and ``skip`` to exclude properties.

Connecting a subset of properties
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``only`` parameter accepts a set of property names (types are
auto-inferred) or a dict (with explicit type strings or transform
tuples). When ``only`` is provided, no template parsing or property
discovery takes place — only the listed properties are connected:

.. code-block:: python

    # Auto-infer types from descriptors:
    autoconnect_callbacks_to_vue(viewer_state, widget,
                                 only={'x_min', 'x_max', 'x_log'})

    # Explicit types / transforms:
    autoconnect_callbacks_to_vue(viewer_state, widget,
                                 only={'x_min': 'float',
                                       'cmap': ('text', cmap_to_name, name_to_cmap)})

Debugging with comm logging
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Call :func:`enable_comm_logging` at the start of a notebook to log every
comm message exchanged between Python and the browser frontend for all
widgets connected via :func:`autoconnect_callbacks_to_vue` after that point.
Messages are emitted at ``DEBUG`` level on the ``echo`` logger.

.. code-block:: python

    from echo.vue import enable_comm_logging, disable_comm_logging

    enable_comm_logging()   # all future widgets will be logged
    disable_comm_logging()  # stop and unpatch any instrumented widgets

To see the messages, configure the ``echo`` logger. To log to the terminal:

.. code-block:: python

    import logging
    logging.getLogger('echo').setLevel(logging.DEBUG)
    logging.getLogger('echo').addHandler(logging.StreamHandler())

To log to a file (useful in glue-jupyter where stdout may be swallowed):

.. code-block:: python

    import logging
    handler = logging.FileHandler('/tmp/echo.log')
    handler.setFormatter(logging.Formatter('%(message)s'))
    logging.getLogger('echo').setLevel(logging.DEBUG)
    logging.getLogger('echo').addHandler(handler)

Each log line is prefixed with the direction of the message:

* ``[PY->VUE]`` -- state sent from Python to the browser
* ``[VUE->PY]`` -- state received from the browser into Python

This is useful for diagnosing circular update loops, where a value is set
in Python, propagated to Vue, modified (e.g. by rounding), sent back, and
triggers another update. Such loops show up as a rapid sequence of
alternating ``[PY->VUE]`` / ``[VUE->PY]`` lines with the same keys.
