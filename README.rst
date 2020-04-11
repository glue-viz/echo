|Azure Status| |Coverage status|

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

.. |Azure Status| image:: https://dev.azure.com/glue-viz/echo/_apis/build/status/glue-viz.echo?branchName=master
   :target: https://dev.azure.com/glue-viz/echo/_build/latest?definitionId=4&branchName=master
.. |Coverage Status| image:: https://codecov.io/gh/glue-viz/echo/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/glue-viz/echo

