from piccolo.conf.apps import Finder


def show_all():
    """
    Lists all registered Piccolo apps.
    """
    app_registry = Finder().get_app_registry()

    print("Registered apps:")

    for app_path in app_registry.apps:
        print(app_path)
