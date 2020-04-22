def show_all():
    """
    Lists all registered Piccolo apps.
    """
    try:
        import piccolo_conf
    except ImportError:
        print("Unable to import piccolo_conf")

    app_registry = getattr(piccolo_conf, "APP_REGISTRY")

    print("Registered apps:")

    for app_path in app_registry.apps:
        print(app_path)
