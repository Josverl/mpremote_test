from pathlib import Path
from typing import List, Tuple
import pytest
import subprocess
from mpflash.mpremoteboard import MPRemoteBoard
import random, string

from collect_boards import boards
from helpers import mcu_file_exists,  copy_and_verify_file


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
