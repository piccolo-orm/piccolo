"""
Backward compat shim
"""

import warnings

from .._compat import properties


NonDataProperty = properties.NonDataProperty
ClassProperty = properties.classproperty


warnings.warn(
    "Properties from keyring.util are no longer supported. "
    "Use jaraco.classes.properties instead.",
    DeprecationWarning,
)
