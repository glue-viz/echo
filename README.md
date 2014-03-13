echo
====

Callback Properties in Python

Echo is a small library for making attaching callback functions
to property value changes. For example:

```
class Switch(object):
    state = CallbackProperty('off')

def report_change(state):
    print 'the switch is %s' % state

s = Switch()
add_callback(s, 'state', report_change)

s.state = 'on'  # prints 'the swtich is on'
```

CalllbackProperties can also be built using decorators

```
class Switch(object):

      @callback_property
      def state(self):
        return self._state

      @state.setter
      def state(self, value):
          if value not in ['on', 'off']:
              raise ValueError("invalid setting")
          self._value = state
```

Full documentation is avilable [here](https://echo.rtfd.org/)