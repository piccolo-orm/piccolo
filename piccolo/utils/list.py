import typing as t

ElementType = t.TypeVar("ElementType")


def flatten(
    items: t.Sequence[t.Union[ElementType, t.List[ElementType]]]
) -> t.List[ElementType]:
    """
    Takes a sequence of elements, and flattens it out. For example::

        >>> flatten(['a', ['b', 'c']])
        ['a', 'b', 'c']

    We need this for situations like this::

        await Band.select(Band.name, Band.manager.all_columns())

    """
    _items: t.List[ElementType] = []
    for item in items:
        if isinstance(item, list):
            _items.extend(item)
        else:
            _items.append(item)

    return _items
