.. currentmodule:: echo

Echo: Callback Properties in Python
===================================

Echo is a tiny python module to create
properties that you can attach callback functions to::

    from echo import CallbackProperty, add_callback

    class Switch(object):
        state = CallbackProperty('off')

    def alert(value):
        print "The switch is %s" % value

    s = Switch()
    add_callback(s, 'state', alert)

    b.state  # 'off'
    b.state = 'on'  # print 'The switch is on'
    assert b.state == 'on'
    b.state = 'off' # print 'The switch is off'

The main features of Echo are:

* A simple, property-like interface to monitor state changes
* Decorator syntax to create callback property getter/setter methods, similar to ``@property``
* Context managers to delay or ignore callback events
* Lightweight codebase (a single file easily embedded in other projects)

Installation
------------
You can install echo from PyPI via pip or easy_install::

    pip install echo
    easy_install echo

Quick Start
-----------
There are two syntaxes for creating callback properties. The first
option is to create a CallbackProperty instance at the class level::

    class Foo(object):
        bar = CallbackProperty(5)  # initial value is 5
        baz = CallbackProperty()   # intial value is None

These behave like normal instance attributes. Altnernatively,
you can use the decorator syntax to implement custom getting and setting
logic::

    class Foo(object):
        @callback_property
        def bar(self):
            ... getter function ....

        @bar.setter(self, value):
           ... setter function ...

.. note:: This syntax uses the lower case :func:`callback_property` decorator instead of the CamelCalse :class:`CallbackProperty` class.

To attach a function to a callback property, use the :func:`add_callback` function::

    def callback(new_value):
        print 'new value is', new_value
    f = Foo()
    add_callback(f, 'bar', callback)
    f.bar = 10  # prints 'new value is 10'

.. note:: The callback property is referred to by name, as a string.

You can also write callbacks that receive both the old and new value of the property, by setting ``echo_old=True`` in :func:`add_callback`::

    def callback(old, new):
        print 'changed from %s to %s' % (old, new)

    f = Foo()
    add_callback(f, 'bar', callback, echo_old=True)
    f.bar = 10  # prints 'changed from 5 to 10'

Delaying, ignoring, and removing callbacks
------------------------------------------
Callback functions can be removed with :func:`remove_callback`::

    remove_callback(f, 'bar', callback)

The :func:`ignore_callback` and :func:`delay_callback` context managers
temporarily disable callbacks from being called::

    with delay_callback(f, 'bar'):
        f.bar = 10
        f.bar = 20
        f.bar = 30

Inside the context manager, none of the callbacks for ``f.bar`` will be called
-- this is useful in situations where you might be making temporary,
incremental changes to a callback property. The difference between
:func:`delay_callback` and :func:`ignore_callback` is whether any
callbacks will be invoked at the end of the context block. Callbacks are
never triggered inside :func:`ignore_callback`, where as they are triggered
a single time inside :func:`delay_callback` if the final state has changed.


API
===

.. autofunction:: callback_property
.. autofunction:: add_callback
.. autofunction:: remove_callback
.. autofunction:: delay_callback
.. autofunction:: ignore_callback
