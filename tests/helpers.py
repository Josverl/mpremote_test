from pathlib import Path
from typing import Dict, List, Tuple
import subprocess, json
from mpflash.mpremoteboard import MPRemoteBoard
import binascii
import hashlib


def mcu_file_size(r, file_name):
    lines = [x for x in r[1] if f" {file_name}\n" in x]
    if not lines:
        raise FileNotFoundError(f"File {file_name} not found")
    line = lines[0]  # should be only one
    size = int(line.split()[0])
    return size


def mcu_file_exists(result: Tuple, file_name: str):
    return any(f" {file_name}\n" in l for l in result[1])


def listdir(comport: str, folder, *, hash=False) -> Dict[str, Dict]:
    """run the listdir script on the remote board and return the file info as a list of dictionaries"""
    cmd = [
        "mpremote",
        "connect",
        comport,
        "run",
        "tests/scripts/listdir_json.py",
        "exec",
        f"print(listdir('{folder}',sub=True, hash={hash},JSON=True))",
    ]
    r = subprocess.run(
        cmd,
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


def copy_and_verify_file(
    board: MPRemoteBoard,
    shared_datadir: Path,
    dest_folder: str,
    file: Path,
    dest_file_name: str = "",
    cleanup: bool = True,
):
    """Copy a file to the remote board and verify that it is there and has the same content"""
    dest_file_name = dest_file_name or file.name
    r = board.run_command(f"cp {file.as_posix()} :{dest_folder}{dest_file_name}")
    assert r[0] == 0

    mcu_files = listdir(board.serialport, "/", hash=True)
    expected_name = expected_remote_name(
        board, file.relative_to(file.parent), dest_folder, mcu_files
    )
    # # is file listed as a remote file ( in the dest_folder)
    assert expected_name in mcu_files
    # # check the file size
    assert mcu_files[expected_name]["size"] == file.stat().st_size
    # compare the file content using a sha256 hash
    with open(file, "rb") as f:
        h = hashlib.sha256(f.read())
    file_hash = binascii.hexlify(h.digest()).decode("utf-8")
    assert mcu_files[expected_name]["hash"] == file_hash

    if cleanup:
        r = board.run_command(f"rm :{dest_folder}{dest_file_name}")


def expected_remote_name(
    board: MPRemoteBoard, item: Path, dest_folder: str, mcu_files: Dict[str, Dict]
):
    """Get the expected remote file name, taking into account the
    board type, the dest_folder and the mount points
    """
    expected_name = dest_folder + item.as_posix()
    # if not specified the stm32 can use /flash or /sd ( or other mounts)
    if not dest_folder:
        if board.port in ["stm32"]:
            for mount in ["/sd", "/flash", ""]:  # perhaps the last should be "."
                if f"{mount}/{expected_name}" in mcu_files:
                    expected_name = f"{mount}/{expected_name}"
                    break
        else:
            # other ports host the files in the root
            expected_name = f"/{expected_name}"
    return expected_name
