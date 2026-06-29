import os

def cd(path: str) -> None:
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")
    # except NotADirectoryError:
    #     print(f"cd: {path}: Not a directory")
    # except PermissionError:
    #     print(f"cd: {path}: Permission denied")
