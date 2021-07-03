import inspect


def repr_class_instance(class_instance: object) -> str:
    """
    Piccolo uses code generation for creating migrations. This function takes
    a class instance, and generates a string representation for it, which can
    be used in a migration file.
    """
    init_arg_names = [
        i
        for i in inspect.signature(
            class_instance.__class__.__init__
        ).parameters.keys()
        if i not in ("self", "args", "kwargs")
    ]
    args_dict = {}
    for arg_name in init_arg_names:
        value = class_instance.__dict__.get(arg_name)
        args_dict[arg_name] = value

    args_str = ", ".join(
        [f"{key}={value.__repr__()}" for key, value in args_dict.items()]
    )
    return f"{class_instance.__class__.__name__}({args_str})"
