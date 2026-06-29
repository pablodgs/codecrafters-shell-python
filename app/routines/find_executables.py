import os

def find_executables(path: str) -> dict[str, str]:
    list_of_path_directories: list[str] = path.split(os.pathsep)
    map_of_executables: dict[str, str] = {}
    for directory in list_of_path_directories:
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    map_of_executables[file] = file_path
    return map_of_executables
