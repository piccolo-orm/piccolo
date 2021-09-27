def get_fixed_length_string(string: str, length=20) -> str:
    """
    Add spacing to the end of the string so it's a fixed length.
    """
    if len(string) > length:
        return string[: length - 3] + "..."
    spacing = "".join(" " for i in range(length - len(string)))
    return f"{string}{spacing}"
