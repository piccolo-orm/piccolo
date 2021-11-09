try:
    from graphlib import CycleError, TopologicalSorter  # type: ignore
except ImportError:
    # For version < Python 3.9
    from ._graphlib import CycleError, TopologicalSorter  # type: ignore
