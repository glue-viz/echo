__all__ = ['CallbackPropertyAlias']


class CallbackPropertyAlias(object):
    """
    An alias for a CallbackProperty that redirects access to a target property.

    This is useful for renaming callback properties while maintaining backwards
    compatibility. Optionally emits deprecation warnings when the alias is used.

    Parameters
    ----------
    target : str
        The name of the target property to redirect to
    deprecated : bool, optional
        If `True`, emit a deprecation warning when the alias is accessed.
        Defaults to `False` (silent alias).
    warning : str, optional
        A custom warning message. If not provided, a default message will be
        generated. Setting this implies ``deprecated=True``.

    Examples
    --------

    ::

        class Foo(HasCallbackProperties):
            # New property name
            line_color = CallbackProperty('red')

            # Silent alias for backwards compatibility
            linecolor = CallbackPropertyAlias('line_color')

            # Deprecated alias with warning
            lc = CallbackPropertyAlias('line_color', deprecated=True)

    """

    def __init__(self, target, deprecated=False, warning=None):
        self._target = target
        # Setting a custom warning message implies deprecated=True
        self._deprecated = deprecated or (warning is not None)
        self._warning = warning
        self._owner = None
        self._name = None

    def __set_name__(self, owner, name):
        self._owner = owner
        self._name = name

    def _warn(self):
        if self._deprecated:
            import warnings
            message = self._warning or f"'{self._name}' is deprecated, use '{self._target}' instead"
            warnings.warn(message, DeprecationWarning, stacklevel=3)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        self._warn()
        return getattr(instance, self._target)

    def __set__(self, instance, value):
        self._warn()
        setattr(instance, self._target, value)

    def __getattr__(self, attr):
        # Proxy attribute access to the target property (e.g., for
        # SelectionCallbackProperty.get_choices, set_choices, etc.)
        if attr.startswith('_'):
            raise AttributeError(attr)
        if self._owner is None:
            raise AttributeError(
                f"Cannot access '{attr}' before class is fully defined")
        target_prop = getattr(self._owner, self._target)
        return getattr(target_prop, attr)

    @property
    def _target_property(self):
        """Return the target CallbackProperty object."""
        if self._owner is None:
            return None
        return getattr(self._owner, self._target)
