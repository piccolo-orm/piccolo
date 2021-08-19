def get_fixed_length_string(string: str, length=20) -> str:
    """
    Add spacing to the end of the string so it's a fixed length.
    """
    if len(string) > length:
        fixed_length_string = string[: length - 3] + "..."
    else:
        spacing = "".join([" " for i in range(length - len(string))])
        fixed_length_string = f"{string}{spacing}"

    return fixed_length_string
