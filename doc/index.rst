Echo: Callback Properties in Python
===================================

Overview
--------

Echo is a small Python module to create properties that you can attach callback
functions to::

  >>> from echo import CallbackProperty, add_callback

  >>> class Switch(object):
  ...     state = CallbackProperty('off')

  >>> def alert(value):
  ...     print("The switch is %s" % value)

  >>> s = Switch()
  >>> add_callback(s, 'state', alert)
  >>> s.state
  'off'
  >>> s.state = 'on'
  The switch is on
  >>> s.state
  'on'
  >>> s.state = 'off'
  The switch is off

The main features of Echo are:

* A simple, property-like interface to monitor state changes

* Decorator syntax to create callback property getter/setter methods, similar to
  ``@property``

* Context managers to delay or ignore callback events

* Helper functions to connect callback properties to GUI elements (at the moment
  only Qt is supported)

User guide
----------

.. toctree::
   :maxdepth: 1

   installation
   core
   gui
   api
