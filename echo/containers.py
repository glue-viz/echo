from . import CallbackProperty, HasCallbackProperties
from .callback_container import CallbackContainer

__all__ = ['CallbackList', 'CallbackDict',
           'ListCallbackProperty', 'DictCallbackProperty']


class ContainerMixin:

    def _prepare_add(self, value):
        if isinstance(value, list):
            value = CallbackList(self.notify_all, value)
        elif isinstance(value, dict):
            value = CallbackDict(self.notify_all, value)
        if isinstance(value, HasCallbackProperties):
            value.add_global_callback(self.notify_all)
        elif isinstance(value, (CallbackList, CallbackDict)):
            value.callback = self.notify_all
        return value

    def _cleanup_remove(self, value):
        if isinstance(value, HasCallbackProperties):
            value.remove_global_callback(self.notify_all)
        elif isinstance(value, (CallbackList, CallbackDict)):
            value.callbacks.remove(self.notify_all)


class CallbackList(list, ContainerMixin):
    """
    A list that calls a callback function when it is modified.

    The first argument should be the callback function (which takes no
    arguments), and subsequent arguments are as for `list`.
    """

    def __init__(self, callback, *args, **kwargs):
        super(CallbackList, self).__init__(*args, **kwargs)
        self.callbacks = CallbackContainer()
        self.callbacks.append(callback)
        for index, value in enumerate(self):
            super().__setitem__(index, self._prepare_add(value))

    def notify_all(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def __repr__(self):
        return "<CallbackList with {0} elements>".format(len(self))

    def append(self, value):
        super(CallbackList, self).append(self._prepare_add(value))
        self.notify_all()

    def extend(self, iterable):
        iterable = [self._prepare_add(value) for value in iterable]
        super(CallbackList, self).extend(iterable)
        self.notify_all()

    def insert(self, index, value):
        super(CallbackList, self).insert(index, self._prepare_add(value))
        self.notify_all()

    def pop(self, index=-1):
        result = super(CallbackList, self).pop(index)
        self._cleanup_remove(result)
        self.notify_all()
        return result

    def remove(self, value):
        super(CallbackList, self).remove(value)
        self._cleanup_remove(value)
        self.notify_all()

    def reverse(self):
        super(CallbackList, self).reverse()
        self.notify_all()

    def sort(self, key=None, reverse=False):
        super(CallbackList, self).sort(key=key, reverse=reverse)
        self.notify_all()

    def __setitem__(self, slc, new_value):

        old_values = self[slc]
        if not isinstance(slc, slice):
            old_values = [old_values]

        for old_value in old_values:
            self._cleanup_remove(old_value)

        if isinstance(slc, slice):
            new_value = [self._prepare_add(value) for value in new_value]
        else:
            new_value = self._prepare_add(new_value)

        super(CallbackList, self).__setitem__(slc, new_value)
        self.notify_all()

    def clear(self):
        for item in self:
            self._cleanup_remove(item)
        super(CallbackList, self).clear()
        self.notify_all()


class CallbackDict(dict, ContainerMixin):
    """
    A dictionary that calls a callback function when it is modified.

    The first argument should be the callback function (which takes no
    arguments), and subsequent arguments are passed to `dict`.
    """

    def __init__(self, callback, *args, **kwargs):
        super(CallbackDict, self).__init__(*args, **kwargs)
        self.callbacks = CallbackContainer()
        self.callbacks.append(callback)
        for key, value in self.items():
            super().__setitem__(key, self._prepare_add(value))

    def notify_all(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)

    def clear(self):
        for value in self.values():
            self._cleanup_remove(value)
        super().clear()
        self.notify_all()

    def popitem(self):
        result = super().popitem()
        self._cleanup_remove(result)
        self.notify_all()
        return result

    def update(self, *args, **kwargs):
        values = {}
        values.update(*args, **kwargs)
        for key, value in values.items():
            values[key] = self._prepare_add(value)
        super().update(values)
        self.notify_all()

    def pop(self, *args, **kwargs):
        result = super().pop(*args, **kwargs)
        self._cleanup_remove(result)
        self.notify_all()
        return result

    def __setitem__(self, key, value):
        if key in self:
            self._cleanup_remove(self[key])
        super().__setitem__(key, self._prepare_add(value))
        self.notify_all()

    def __repr__(self):
        return f"<CallbackDict with {len(self)} elements>"


class dynamic_callback:

    function = None

    def __call__(self, *args, **kwargs):
        self.function(*args, **kwargs)


class ListCallbackProperty(CallbackProperty):
    """
    A list property that calls callbacks when its contents are modified
    """

    def _default_getter(self, instance, owner=None):
        if instance not in self._values:
            self._default_setter(instance, self._default or [])
        return super(ListCallbackProperty, self)._default_getter(instance, owner)

    def _default_setter(self, instance, value):

        if not isinstance(value, list):
            raise TypeError('callback property should be a list')

        dcb = dynamic_callback()

        wrapped_list = CallbackList(dcb, value)

        def callback(*args, **kwargs):
            self.notify(instance, wrapped_list, wrapped_list)

        dcb.function = callback

        super(ListCallbackProperty, self)._default_setter(instance, wrapped_list)


class DictCallbackProperty(CallbackProperty):
    """
    A dictionary property that calls callbacks when its contents are modified
    """
    def _default_getter(self, instance, owner=None):
        if instance not in self._values:
            self._default_setter(instance, self._default or {})
        return super()._default_getter(instance, owner)

    def _default_setter(self, instance, value):

        if not isinstance(value, dict):
            raise TypeError("Callback property should be a dictionary.")

        dcb = dynamic_callback()

        wrapped_dict = CallbackDict(dcb, value)

        def callback(*args, **kwargs):
            self.notify(instance, wrapped_dict, wrapped_dict)

        dcb.function = callback

        super()._default_setter(instance, wrapped_dict)
