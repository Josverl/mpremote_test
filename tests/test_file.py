from pathlib import Path
from typing import List, Tuple
import pytest
import subprocess
from mpflash.mpremoteboard import MPRemoteBoard


boards = [MPRemoteBoard(comport) for comport in MPRemoteBoard.connected_boards()]
for board in boards:
    try:
        board.get_mcu_info()
    except Exception as e:
        print(f"Error: {e}")
        boards.remove(board)


@pytest.mark.parametrize(
    "board", boards, ids=[str(board.port or board.serialport) for board in boards]
)
@pytest.mark.parametrize(
    "file_name",
    [
        "foo.txt",
        "test.jpg",
    ],
)
@pytest.mark.parametrize(
    "dest_folder",
    [
        "",
        "/flash",
        "/sd",
    ],
)
def test_copy_file_to(
    board: MPRemoteBoard,
    shared_datadir: Path,
    file_name: str,
    dest_folder: str,
):

    if dest_folder:
        # check if the remote MCU supports the /flash folder
        if dest_folder.startswith("/"):
            r = board.run_command("ls /")
            if not mcu_file_exists(r, f"{dest_folder[1:]}/"):
                pytest.skip(f"Remote MCU does not support  {dest_folder} ")

        if not dest_folder.endswith("/"):
            dest_folder += "/"
    file = shared_datadir / file_name
    try:
        r = board.run_command(f"cp {file.as_posix()} :{dest_folder}{file_name}")
        assert r[0] == 0

        # is file listed as a remote file ( in the dest_folder)
        r = board.run_command(f"ls :{dest_folder}")
        assert mcu_file_exists(r, file_name)

        # get the line with the file name
        size = mcu_file_size(r, f"{file_name}")
        # check the file size
        assert size == file.stat().st_size

        # create a return folder and copy the file back
        return_folder = shared_datadir / "return"
        return_folder.mkdir(exist_ok=True)
        r = board.run_command(f"cp :{dest_folder}{file_name} {return_folder.as_posix()}")
        assert r[0] == 0
        # check if the file is there
        assert (return_folder / file_name).exists()
        # check if the file has the same content
        assert (return_folder / file_name).read_bytes() == file.read_bytes()
    finally:
        board.run_command(f"rm :{file_name}")


def mcu_file_size(r, file_name):
    lines = [x for x in r[1] if f" {file_name}\n" in x]
    if not lines:
        raise FileNotFoundError(f"File {file_name} not found")
    line = lines[0]  # should be only one
    size = int(line.split()[0])
    return size


def mcu_file_exists(result: Tuple, file_name: str):
    return any(f" {file_name}\n" in l for l in result[1])


def test_version():

    r = subprocess.run(["mpremote", "--version"], capture_output=True, universal_newlines=True)
    assert r.returncode == 0
    out = r.stdout.splitlines()
    assert out[0].startswith("mpremote 1.24.0")
