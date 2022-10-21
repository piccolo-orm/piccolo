"""The main parsing routine."""

from docstring_parser import epydoc, google, numpydoc, rest
from docstring_parser.common import (
    Docstring,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)

_STYLE_MAP = {
    DocstringStyle.REST: rest,
    DocstringStyle.GOOGLE: google,
    DocstringStyle.NUMPYDOC: numpydoc,
    DocstringStyle.EPYDOC: epydoc,
}


def parse(text: str, style: DocstringStyle = DocstringStyle.AUTO) -> Docstring:
    """Parse the docstring into its components.

    :param text: docstring text to parse
    :param style: docstring style
    :returns: parsed docstring representation
    """
    if style != DocstringStyle.AUTO:
        return _STYLE_MAP[style].parse(text)

    rets = []
    for module in _STYLE_MAP.values():
        try:
            rets.append(module.parse(text))
        except ParseError as ex:
            exc = ex

    if not rets:
        raise exc

    return sorted(rets, key=lambda d: len(d.meta), reverse=True)[0]


def compose(
    docstring: Docstring,
    style: DocstringStyle = DocstringStyle.AUTO,
    rendering_style: RenderingStyle = RenderingStyle.COMPACT,
    indent: str = "    ",
) -> str:
    """Render a parsed docstring into docstring text.

    :param docstring: parsed docstring representation
    :param style: docstring style to render
    :param indent: the characters used as indentation in the docstring string
    :returns: docstring text
    """
    module = _STYLE_MAP[
        docstring.style if style == DocstringStyle.AUTO else style
    ]
    return module.compose(
        docstring, rendering_style=rendering_style, indent=indent
    )
