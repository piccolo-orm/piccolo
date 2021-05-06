import inflection


def _camel_to_snake(string: str):
    """
    Convert CamelCase to snake_case.
    """
    return inflection.underscore(string)
