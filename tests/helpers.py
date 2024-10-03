from typing import Tuple


def mcu_file_size(r, file_name):
    lines = [x for x in r[1] if f" {file_name}\n" in x]
    if not lines:
        raise FileNotFoundError(f"File {file_name} not found")
    line = lines[0]  # should be only one
    size = int(line.split()[0])
    return size


def mcu_file_exists(result: Tuple, file_name: str):
    return any(f" {file_name}\n" in l for l in result[1])
