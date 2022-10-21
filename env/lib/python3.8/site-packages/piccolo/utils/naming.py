import inflection


def _camel_to_snake(string: str):
    """
    Convert CamelCase to snake_case.
    """
    return inflection.underscore(string)


def _snake_to_camel(string: str):
    """
    Convert snake_case to CamelCase.
    """
    return inflection.camelize(string)
