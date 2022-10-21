"""
This module provides :class:`.GitIgnoreSpec` which replicates
*.gitignore* behavior.
"""

from typing import (
	AnyStr,
	Callable,
	Collection,
	Iterable,
	TYPE_CHECKING,
	Union)

from .pathspec import (
	PathSpec)
from .pattern import (
	Pattern)
from .patterns.gitwildmatch import (
	GitWildMatchPattern)
from .util import (
	_is_iterable)


class GitIgnoreSpec(PathSpec):
	"""
	The :class:`GitIgnoreSpec` class extends :class:`PathSpec` to
	replicate *.gitignore* behavior.
	"""

	def __eq__(self, other: 'Self') -> bool:
		"""
		Tests the equality of this gitignore-spec with *other*
		(:class:`GitIgnoreSpec`) by comparing their :attr:`~PathSpec.patterns`
		attributes. A non-:class:`GitIgnoreSpec` will not compare equal.
		"""
		if isinstance(other, GitIgnoreSpec):
			return super().__eq__(other)
		elif isinstance(other, PathSpec):
			return False
		else:
			return NotImplemented

	@classmethod
	def from_lines(
		cls,
		lines: Iterable[AnyStr],
		pattern_factory: Union[str, Callable[[AnyStr], Pattern], None] = None,
	) -> 'Self':
		"""
		Compiles the pattern lines.

		*lines* (:class:`~collections.abc.Iterable`) yields each uncompiled
		pattern (:class:`str`). This simply has to yield each line so it can
		be a :class:`io.TextIOBase` (e.g., from :func:`open` or
		:class:`io.StringIO`) or the result from :meth:`str.splitlines`.

		*pattern_factory* can be :data:`None`, the name of a registered
		pattern factory (:class:`str`), or a :class:`~collections.abc.Callable`
		used to compile patterns. The callable must accept an uncompiled
		pattern (:class:`str`) and return the compiled pattern (:class:`.Pattern`).
		Default is :data:`None` for :class:`.GitWildMatchPattern`).

		Returns the :class:`GitIgnoreSpec` instance.
		"""
		if pattern_factory is None:
			pattern_factory = GitWildMatchPattern

		elif (isinstance(lines, str) or callable(lines)) and _is_iterable(pattern_factory):
			# Support reversed order of arguments from PathSpec.
			pattern_factory, lines = lines, pattern_factory

		self = super().from_lines(pattern_factory, lines)
		return self  # type: ignore

	@staticmethod
	def _match_file(
		patterns: Collection[GitWildMatchPattern],
		file: str,
	) -> bool:
		"""
		Matches the file to the patterns.

		.. NOTE:: Subclasses of :class:`.PathSpec` may override this
		   method as an instance method. It does not have to be a static
		   method.

		*patterns* (:class:`~collections.abc.Iterable` of :class:`~pathspec.pattern.Pattern`)
		contains the patterns to use.

		*file* (:class:`str`) is the normalized file path to be matched
		against *patterns*.

		Returns :data:`True` if *file* matched; otherwise, :data:`False`.
		"""
		out_matched = False
		out_priority = 0
		for pattern in patterns:
			if pattern.include is not None:
				match = pattern.match_file(file)
				if match is not None:
					# Pattern matched.

					# Check for directory marker.
					dir_mark = match.match.group('ps_d')
					if dir_mark:
						# Pattern matched by a directory pattern.
						priority = 1
					else:
						# Pattern matched by a file pattern.
						priority = 2

					if priority >= out_priority:
						out_matched = pattern.include
						out_priority = priority

		return out_matched


if TYPE_CHECKING:
	try:
		from typing import Self
	except ImportError:
		try:
			from typing_extensions import Self
		except ImportError:
			Self = GitIgnoreSpec
