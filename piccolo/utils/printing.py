def get_fixed_length_string(string: str, length=20) -> str:
    """
    Add spacing to the end of the string so it's a fixed length.
    """
    spacing = "".join([" " for i in range(length - len(string))])
    fixed_length_string = f"{string}{spacing}"
    return fixed_length_string
