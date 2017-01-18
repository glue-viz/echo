|Travis Build Status| |AppVeyor Build status| |Coveralls coverage|

echo: Callback Properties in Python
===================================

Echo is a small library for attaching callback functions to property
state changes. For example:

::

    class Switch(object):
        state = CallbackProperty('off')

    def report_change(state):
        print 'the switch is %s' % state

    s = Switch()
    add_callback(s, 'state', report_change)

    s.state = 'on'  # prints 'the switch is on'

CalllbackProperties can also be built using decorators

::

    class Switch(object):

          @callback_property
          def state(self):
            return self._state

          @state.setter
          def state(self, value):
              if value not in ['on', 'off']:
                  raise ValueError("invalid setting")
              self._state = value

Full documentation is avilable `here <http://echo.readthedocs.org/>`__

.. |Travis Build Status| image:: https://travis-ci.org/glue-viz/echo.svg?branch=master
   :target: https://travis-ci.org/glue-viz/echo
.. |AppVeyor Build status| image:: https://ci.appveyor.com/api/projects/status/rg4p7facvxcdu6jg/branch/master?svg=true
   :target: https://ci.appveyor.com/project/glue-viz/echo
.. |Coveralls coverage| image:: https://coveralls.io/repos/glue-viz/echo/badge.svg
   :target: https://coveralls.io/r/glue-viz/echo


