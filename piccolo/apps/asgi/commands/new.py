import colorama
import os
import shutil
import typing as t

import black
import jinja2


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates/starlette/")
SERVERS = ["uvicorn", "Hypercorn"]
ENGINES = ["postgres", "sqlite"]


def print_instruction(message: str):
    print(f"{colorama.Fore.CYAN}{message}{colorama.Fore.RESET}")


def get_options_string(options: t.List[str]):
    return ", ".join(
        [f"{name} [{index}]" for index, name in enumerate(options)]
    )


def new():
    """
    Create a basic ASGI app, including Piccolo, routing, and an admin.
    """
    tree = os.walk(TEMPLATE_DIR)

    print_instruction("Which server?")
    server = input(f"{get_options_string(SERVERS)}\n") or 0

    print_instruction("Which engine?")
    engine = input(f"{get_options_string(ENGINES)}\n") or 0

    template_context = {
        "server": SERVERS[int(server)],
        "engine": ENGINES[int(engine)],
    }

    for directory in tree:
        dir_path, sub_dir_names, file_names = directory  # type: ignore

        output_dir_path = os.path.join(
            os.getcwd(), dir_path.split(TEMPLATE_DIR)[-1]
        )

        if not os.path.exists(output_dir_path):
            folder_name = output_dir_path.split("/")[-1]
            if folder_name.startswith("_") or folder_name.startswith("."):
                continue
            os.mkdir(dir_path)

        for sub_dir_name in sub_dir_names:
            if sub_dir_name.startswith("_"):
                continue

            sub_dir_path = os.path.join(output_dir_path, sub_dir_name)
            if not os.path.exists(sub_dir_path):
                os.mkdir(sub_dir_path)

        for file_name in file_names:
            if file_name.startswith("_"):
                continue

            extension = file_name.rsplit(".")[0]
            if extension in ("pyc",):
                continue

            if file_name.endswith(".jinja"):
                output_file_name = file_name.replace(".jinja", "")

                with open(os.path.join(dir_path, file_name)) as f:
                    file_contents = f.read()

                template = jinja2.Template(file_contents)
                output_contents = template.render(**template_context)

                if output_file_name.endswith(".py"):
                    try:
                        output_contents = black.format_str(
                            output_contents,
                            mode=black.FileMode(line_length=80),
                        )
                    except Exception as exception:
                        print(f"Problem processing {output_file_name}")
                        raise exception

                with open(
                    os.path.join(output_dir_path, output_file_name), "w"
                ) as f:
                    f.write(output_contents)
            else:
                if file_name.endswith(".jinja_raw"):
                    output_file_name = file_name.replace(
                        ".jinja_raw", ".jinja"
                    )
                else:
                    output_file_name = file_name

                shutil.copy(
                    os.path.join(dir_path, file_name),
                    os.path.join(output_dir_path, output_file_name),
                )

    print(
        "Run `pip install -r requirements.txt` and `python app.py` to get "
        "started."
    )
