from pathlib import Path
from typing import List, Tuple
import pytest
import subprocess
from mpflash.mpremoteboard import MPRemoteBoard
import random, string

from collect_boards import boards
from helpers import mcu_file_exists, mcu_file_size


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
        copy_and_verify_file(
            board,
            shared_datadir,
            dest_folder,
            file,
            # file_name,
        )
    finally:
        board.run_command(f"rm :{file_name}")


def copy_and_verify_file(
    board: MPRemoteBoard,
    shared_datadir: Path,
    dest_folder: str,
    file: Path,
    dest_file_name: str = "",
):
    """Copy a file to the remote board and verify that it is there and has the same content"""
    dest_file_name = dest_file_name or file.name
    r = board.run_command(f"cp {file.as_posix()} :{dest_folder}{dest_file_name}")
    assert r[0] == 0

    # is file listed as a remote file ( in the dest_folder)
    r = board.run_command(f"ls :{dest_folder}")
    assert mcu_file_exists(r, dest_file_name)

    # get the line with the file name
    size = mcu_file_size(r, f"{dest_file_name}")
    # check the file size
    assert size == file.stat().st_size

    # create a return folder and copy the file back
    return_folder = shared_datadir / "return"
    return_folder.mkdir(exist_ok=True)
    r = board.run_command(f"cp :{dest_folder}{dest_file_name} {return_folder.as_posix()}")
    assert r[0] == 0
    # check if the file is there
    assert (return_folder / dest_file_name).exists()
    # check if the file has the same content
    assert (return_folder / dest_file_name).read_bytes() == file.read_bytes()


@pytest.mark.parametrize(
    "board", boards, ids=[str(board.port or board.serialport) for board in boards]
)
@pytest.mark.parametrize(
    "dest_folder",
    [
        "",
        # "/flash",
        # "/sd",
    ],
)
@pytest.mark.parametrize("length", [1, 100, 256 + 1, 512 + 1, 2048 + 1])
def test_copy_random_content(
    board: MPRemoteBoard,
    tmp_path: Path,
    dest_folder: str,
    length: int,
):

    if dest_folder:
        # check if the remote MCU supports the /flash folder
        if dest_folder.startswith("/"):
            r = board.run_command("ls /")
            if not mcu_file_exists(r, f"{dest_folder[1:]}/"):
                pytest.skip(f"Remote MCU does not support  {dest_folder} ")

        if not dest_folder.endswith("/"):
            dest_folder += "/"
    file_name = "random.utf"
    tmp_file = tmp_path / file_name
    tmp_file.write_text(generate_random_unicode_text(length), encoding="utf-8")
    try:
        copy_and_verify_file(
            board,
            tmp_file.parent,
            dest_folder,
            tmp_file,
            # file_name,
        )
    finally:
        board.run_command(f"rm :{file_name}")


def generate_random_unicode_text(length):
    # Define a range of Unicode characters
    unicode_chars = "".join(chr(i) for i in range(32, 127))  # Basic Latin
    unicode_chars += "".join(chr(i) for i in range(160, 255))  # Latin-1 Supplement
    unicode_chars += "".join(chr(i) for i in range(1024, 1120))  # Cyrillic

    # Generate random text
    random_text = "".join(random.choice(unicode_chars) for _ in range(length))
    return random_text


def test_version():

    r = subprocess.run(["mpremote", "--version"], capture_output=True, universal_newlines=True)
    assert r.returncode == 0
    out = r.stdout.splitlines()
    assert out[0].startswith("mpremote 1.24.0")
