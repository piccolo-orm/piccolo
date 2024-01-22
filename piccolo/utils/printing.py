from typing import List


def get_fixed_length_string(string: str, length: int = 20) -> str:
    """
    Add spacing to the end of the string so it's a fixed length, or truncate
    if it's too long.
    """
    if len(string) > length:
        return f"{string[: length - 3]}..."
    spacing = "".join(" " for _ in range(length - len(string)))
    return f"{string}{spacing}"


def print_heading(string: str, width: int = 64) -> None:
    """
    Prints out a nicely formatted heading to the console. Useful for breaking
    up the output in large CLI commands.
    """
    print(f"\n{string.upper():^{width}}")
    print("-" * width)


def print_dict_table(data: List[dict], header_separator: bool = False) -> None:
    """
    Prints out a list of dictionaries in tabular form.

    Uses the first list element to extract the column names and their order
    within the row.

    """
    if len(data) == 0:
        raise ValueError("The data must have at least one element.")

    column_names = data[0].keys()
    widths = {column_name: len(column_name) for column_name in column_names}

    for item in data:
        for column in column_names:
            width = len(str(item[column]))
            if width > widths[column]:
                widths[column] = width

    format_string = " | ".join(f"{{:<{widths[w]}}}" for w in column_names)

    print(format_string.format(*[str(w) for w in column_names]))

    if header_separator:
        format_string_sep = "-+-".join(
            [f"{{:<{widths[w]}}}" for w in column_names]
        )
        print(
            format_string_sep.format(*["-" * widths[w] for w in column_names])
        )

    for item in data:
        print(format_string.format(*[str(item[w]) for w in column_names]))
