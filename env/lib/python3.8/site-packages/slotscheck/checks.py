"Slots-related checks and inspection tools"
import platform
from typing import Collection, Iterator, Optional


def slots(c: type) -> Optional[Collection[str]]:
    try:
        slots_raw = c.__dict__["__slots__"]
    except KeyError:
        return None
    if isinstance(slots_raw, str):
        return (slots_raw,)
    elif isinstance(slots_raw, Iterator):
        raise NotImplementedError("Iterator __slots__ not supported. See #22")
    else:
        return slots_raw


def has_slots(c: type) -> bool:
    return "__slots__" in c.__dict__ or not (
        issubclass(c, BaseException) or is_pure_python(c)
    )


def has_slotless_base(c: type) -> bool:
    return not all(map(has_slots, c.__bases__))


def slots_overlap(c: type) -> bool:
    maybe_slots = slots(c)
    if maybe_slots is None:
        return False
    slots_ = set(maybe_slots)
    for ancestor in c.mro()[1:]:
        if not slots_.isdisjoint(slots(ancestor) or ()):
            return True
    return False


def has_duplicate_slots(c: type) -> bool:
    slots_ = slots(c) or ()
    return len(set(slots_)) != len(list(slots_))


# The 'is a pure python class' logic below is adapted
# from https://stackoverflow.com/a/41012823/

# If the active Python interpreter is the official CPython interpreter,
# prefer a more reliable CPython-specific solution guaranteed to succeed.
if platform.python_implementation() == "CPython":
    # Magic number defined by the Python codebase at "Include/object.h".
    Py_TPFLAGS_HEAPTYPE = 1 << 9

    def is_pure_python(cls: type) -> bool:
        "Whether the class is pure-Python or C-based"
        return bool(cls.__flags__ & Py_TPFLAGS_HEAPTYPE)


# Else, fallback to a CPython-agnostic solution typically but *NOT*
# necessarily succeeding. For all real-world objects of interest, this is
# effectively successful. Edge cases exist but are suitably rare.
else:  # pragma: no cover

    def is_pure_python(cls: type) -> bool:
        "Whether the class is pure-Python or C-based"
        return "__dict__" in dir(cls) or hasattr(cls, "__slots__")
