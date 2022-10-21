import pkg_resources

try:
    __version__ = pkg_resources.get_distribution('pip_upgrader').version
except Exception:  # pragma: nocover
    __version__ = 'unknown'
