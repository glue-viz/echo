import sys

from echo import CallbackProperty, HasCallbackProperties


class CallbackList(list):
    """
    A list that calls a callback function when it is modified.

    The first argument should be the callback function (which takes no
    arguments), and subsequent arguments are as for `list`.
    """

    def __init__(self, callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callback = callback

    def append(self, value):
        super().append(value)
        if isinstance(value, HasCallbackProperties):
            value.add_callback('*', self.callback)
        self.callback()

    def extend(self, iterable):
        super().extend(iterable)
        for item in iterable:
            if isinstance(item, HasCallbackProperties):
                item.add_callback('*', self.callback)
        self.callback()

    def insert(self, index, value):
        super().insert(index, value)
        if isinstance(value, HasCallbackProperties):
            value.add_callback('*', self.callback)
        self.callback()

    def pop(self, index=-1):
        result = super().pop(index)
        if isinstance(result, HasCallbackProperties):
            result.remove_callback('*', self.callback)
        self.callback()
        return result

    def remove(self, value):
        if isinstance(value, HasCallbackProperties):
            value.remove_callback('*', self.callback)
        super().remove(value)
        self.callback()

    def reverse(self):
        super().reverse()
        self.callback()

    def sort(self, key=None, reverse=False):
        super().sort(key=key, reverse=reverse)
        self.callback()

    if sys.version_info[0] >= 3:

        def clear(self):
            for item in self:
                if isinstance(item, HasCallbackProperties):
                    item.remove_callback('*', self.callback)
            super().clear()
            self.callback()


class ListCallbackProperty(CallbackProperty):
    """
    A list property that calls callbacks when its contents are modified
    """

    def _default_getter(self, instance, owner=None):
        if instance not in self._values:
            self._default_setter(instance, [])
        return super()._default_getter(instance, owner)

    def _default_setter(self, instance, value):

        if not isinstance(value, list):
            raise TypeError('callback property should be a list')

        def callback(*args):
            self.notify(instance, value, value)

        wrapped_list = CallbackList(callback, value)
        super()._default_setter(instance, wrapped_list)
