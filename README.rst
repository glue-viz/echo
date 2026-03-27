|CI Status| |Coverage Status| |PyPI Version|

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

.. |CI Status| image:: https://github.com/glue-viz/echo/actions/workflows/ci_workflows.yml/badge.svg
   :target: https://github.com/glue-viz/echo/actions/workflows/ci_workflows.yml
.. |Coverage Status| image:: https://codecov.io/gh/glue-viz/echo/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/glue-viz/echo
.. |PyPI Version| image:: https://img.shields.io/pypi/v/echo.svg
   :target: https://pypi.org/project/echo/
