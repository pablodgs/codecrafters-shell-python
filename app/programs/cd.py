import os

def cd(path: str) -> None:
    home: str = os.environ.get("HOME", "")

    if path == "~":
        path = home

    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")
    # except NotADirectoryError:
    #     print(f"cd: {path}: Not a directory")
    # except PermissionError:
    #     print(f"cd: {path}: Permission denied")
