import typing as t

if t.TYPE_CHECKING:
    from ..columns.combination import Where, And, Or  # noqa


Combinable = t.Union['Where', 'And', 'Or']
Iterable = t.Iterable[t.Any]


__all__ = (
    'Combinable',
    'Iterable'
)
