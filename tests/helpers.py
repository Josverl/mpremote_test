from typing import Dict, List, Tuple
import subprocess, json


def mcu_file_size(r, file_name):
    lines = [x for x in r[1] if f" {file_name}\n" in x]
    if not lines:
        raise FileNotFoundError(f"File {file_name} not found")
    line = lines[0]  # should be only one
    size = int(line.split()[0])
    return size


def mcu_file_exists(result: Tuple, file_name: str):
    return any(f" {file_name}\n" in l for l in result[1])


def listdir(comport: str, folder) -> Dict[str, Dict]:
    """run the listdir script on the remote board and return the file info as a list of dictionaries"""

    r = subprocess.run(
        [
            "mpremote",
            "connect",
            comport,
            "run",
            "tests/scripts/listdir_json.py",
            "exec",
            f"print(listdir('{folder}',sub=True, hash=False,JSON=True))",
        ],
        capture_output=True,
    )
    assert r.returncode == 0, f"Error: {r.stdout.decode('utf-8')}"
    data = r.stdout.decode("utf-8", errors="ignore")  # ignore stm32 utf-8 errors
    try:
        file_info = json.loads(data)
        assert isinstance(file_info, dict)
        return file_info
    except json.JSONDecodeError as e:
        print(f"Error: {e}")
        print(f"Data: {data}")
        return {
            "error": {"JSON decode error": str(e), "data": str(data)},
        }


def wipe_filesystem(comport, folder="/"):
    r = subprocess.run(
        [
            "mpremote",
            "connect",
            comport,
            "run",
            "tests/scripts/wipe_fs.py",
            "exec",
            f"wipe_folder('{folder}',sub=True)",
        ],
        capture_output=True,
    )
    data = r.stdout.decode("utf-8", errors="ignore")  # ignore utf-8 errors from stm32
    try:
        file_info = json.loads(data)
        assert isinstance(file_info, dict)
        return file_info
    except json.JSONDecodeError as e:
        print(f"Error: {e}")
        print(f"Data: {data}")
        return {}
