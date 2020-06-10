import os
import shutil

import jinja2


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates/starlette/")


def new(project_name: str = "example_project", app_name: str = "example_app"):
    """
    Create a basic ASGI app, including Piccolo, routing, and an admin.

    :param project_name:
        The name of the new project.

    :param app_name:
        The project will be given an initial app to get you started.

    """
    files = os.walk(TEMPLATE_DIR)

    for file in files:
        dir_path, sub_dir_names, file_names = file  # type: ignore

        output_dir_path = os.path.join(
            os.getcwd(), dir_path.split(TEMPLATE_DIR)[-1]
        )

        if not os.path.exists(output_dir_path):
            os.mkdir(dir_path)

        for sub_dir_name in sub_dir_names:
            if sub_dir_name.startswith("__"):
                continue

            sub_dir_path = os.path.join(output_dir_path, sub_dir_name)
            if not os.path.exists(sub_dir_path):
                os.mkdir(sub_dir_path)

        for file_name in file_names:
            extension = file_name.rsplit(".")[0]
            if extension in ("pyc"):
                continue

            if file_name.endswith(".jinja"):
                output_file_name = file_name.replace(".jinja", "")

                with open(os.path.join(dir_path, file_name)) as f:
                    file_contents = f.read()

                with open(
                    os.path.join(output_dir_path, output_file_name), "w"
                ) as f:
                    f.write(file_contents)
            else:
                shutil.copy(
                    os.path.join(dir_path, file_name),
                    os.path.join(output_dir_path, file_name),
                )
