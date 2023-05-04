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


def batch(
    data: t.List[ElementType], chunk_size: int
) -> t.List[t.List[ElementType]]:
    """
    Breaks the list down into sublists of the given ``chunk_size``. The last
    sublist may have fewer elements than ``chunk_size``::

        >>> batch(['a', 'b', 'c'], 2)
        [['a', 'b'], ['c']]

    :param data:
        The data to break up into sublists.
    :param chunk_size:
        How large each sublist should be.

    """
    # TODO: Replace with itertools.batch when available:
    # https://docs.python.org/3.12/library/itertools.html#itertools.batched

    if chunk_size <= 0:
        raise ValueError("`chunk_size` must be greater than 0.")

    row_count = len(data)

    iterations = int(row_count / chunk_size)
    if row_count % chunk_size > 0:
        iterations += 1

    return [
        data[(i * chunk_size) : ((i + 1) * chunk_size)]  # noqa: E203
        for i in range(0, iterations)
    ]
