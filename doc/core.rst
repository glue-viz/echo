.. currentmodule:: echo

Quick Start
-----------

There are two syntaxes for creating callback properties. The first option is to
create a CallbackProperty instance at the class level::

    class Foo(object):
        bar = CallbackProperty(5)  # initial value is 5
        baz = CallbackProperty()   # intial value is None

These behave like normal instance attributes. Altnernatively, you can use the
decorator syntax (all lowercase and with an underscore) to implement custom
getting and setting logic::

    class Foo(object):

        @callback_property
        def bar(self):
            ... getter function ....

        @bar.setter
        def bar(self, value):
           ... setter function ...

To attach a function to a callback property, use the :func:`add_callback`
function::

    def callback(new_value):
        print('new value is %g' % new_value)

    f = Foo()
    add_callback(f, 'bar', callback)

    # The following will print 'new value is 10'
    f.bar = 10

.. note:: When calling :func:`add_callback`, the callback property is
          referred to by name, as a string.

You can also write callbacks that receive both the old and new value of the
property, by setting ``echo_old=True`` in :func:`add_callback`::

    def callback(old, new):
        print('changed from %s to %s' % (old, new))

    f = Foo()
    add_callback(f, 'bar', callback, echo_old=True)

    # The following will print 'changed from 5 to 10'
    f.bar = 10

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
