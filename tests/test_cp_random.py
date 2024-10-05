from pathlib import Path
from typing import List, Tuple
import pytest
import subprocess
from mpflash.mpremoteboard import MPRemoteBoard
import random, string

from collect_boards import boards
from helpers import mcu_file_exists, copy_and_verify_file
from hypothesis import example, given, reproduce_failure, strategies as st, settings

import contextlib


@pytest.mark.skip("WIP")
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
@settings(deadline=None, print_blob=True)
@given(
    file_name=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=31),
    ext=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=5),
)
@example(file_name="fooji", ext="txt")
# @reproduce_failure("6.112.2", b"AAEQAAEQAA==")
def test_copy_random_name(
    board: MPRemoteBoard,
    # tmp_path: Path,
    dest_folder: str,
    file_name: str,
    ext: str,
):

    if dest_folder:
        # check if the remote MCU supports the /dest folder
        if dest_folder.startswith("/"):
            r = board.run_command("ls /")
            if not mcu_file_exists(r, f"{dest_folder[1:]}/"):
                pytest.skip(f"Remote MCU does not support  {dest_folder} ")

        if not dest_folder.endswith("/"):
            dest_folder += "/"
    base_path = Path("D:\\mypython\\mpremote_test\\tests\\data\\random")
    base_path.mkdir(parents=True, exist_ok=True)
    file = base_path / f"{file_name}.{ext}"

    file.write_text("".join(random.choices(string.printable, k=100)))

    try:
        copy_and_verify_file(
            board,
            base_path,
            dest_folder,
            file,
            # file_name,
            cleanup=True,
        )
    finally:
        with contextlib.suppress(Exception):
            (base_path / "return").unlink()
            board.run_command(f"rm :{file_name}.{ext}")
