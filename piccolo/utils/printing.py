from typing import List


def get_fixed_length_string(string: str, length=20) -> str:
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
    Uses the first list element to extract the
    column names and their order within the row.
    """

    if len(data) < 1:
        print("No data")
        return

    ref_order = [column for column in data[0]]
    width = {column: len(str(column)) for column in ref_order}

    for item in data:
        for column in ref_order:
            if len(str(item[column])) > width[column]:
                width[column] = len(str(item[column]))

    format_string = " | ".join([f"{{:<{width[w]}}}" for w in ref_order])

    print(format_string.format(*[str(w) for w in ref_order]))

    if header_separator:
        format_string_sep = "-+-".join(
            [f"{{:<{width[w]}}}" for w in ref_order]
        )
        print(format_string_sep.format(*["-" * width[w] for w in ref_order]))

    for item in data:
        print(format_string.format(*[str(item[w]) for w in ref_order]))
