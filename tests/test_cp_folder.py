from pathlib import Path
import pytest
from mpflash.mpremoteboard import MPRemoteBoard

from collect_boards import boards
from helpers import mcu_file_exists, listdir, wipe_filesystem


@pytest.mark.parametrize(
    "board", boards, ids=[str(board.port or board.serialport) for board in boards]
)
@pytest.mark.parametrize(
    "folder_name",
    [
        "folder_1",
        "p1_meter",
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
def test_copy_folder_to(
    board: MPRemoteBoard,
    folder_name: str,
    datadir: Path,
    dest_folder: str,
    tmp_path: Path,
):

    if dest_folder:
        # check if the remote MCU supports the /flash folder
        if dest_folder.startswith("/"):
            r = board.run_command("ls /")
            if not mcu_file_exists(r, f"{dest_folder[1:]}/"):
                pytest.skip(f"Remote MCU does not support  {dest_folder} ")

        if not dest_folder.endswith("/"):
            dest_folder += "/"
    folder = datadir / folder_name
    src_content = None
    mcu_files = None
    try:
        # 1st copy
        r = board.run_command(f"cp -r {folder.as_posix()} :{dest_folder}")
        assert r[0] == 0

        # 2nd copy should just report Up to date for all files
        r = board.run_command(f"cp -r {folder.as_posix()} :{dest_folder}")
        assert r[0] == 0
        assert all(l.startswith("Up to date") for l in r[1][1:])

        # is FOLDER listed as a remote file + / ( in the dest_folder)
        r = board.run_command(f"ls :{dest_folder}")
        assert mcu_file_exists(r, folder_name + "/")  # çause it is a folder

        # Recursivly check the content of the folder
        src_content = list(folder.rglob("*"))

        mcu_files = listdir(board.serialport, "/")

        for item in src_content:
            # check if the file exists
            expected_name = dest_folder + item.relative_to(folder.parent).as_posix()
            # if not specified the stm32 can use /flash or /sd ( or other mounts)
            if dest_folder == "":
                if board.port in ["stm32"]:
                    for mount in ["/sd", "/flash"]:
                        if f"{mount}/{expected_name}" in mcu_files:
                            expected_name = f"{mount}/{expected_name}"
                            break
                else:
                    # other ports host the files in the root
                    expected_name = f"/{expected_name}"

            assert expected_name in mcu_files, f"File {expected_name} not found"
            if item.is_dir():
                assert (
                    mcu_files[expected_name]["type"] == "dir"
                ), f"File {expected_name} is not a folder"
                assert (
                    0 == mcu_files[expected_name]["size"]
                ), f"Folder {expected_name} size is not 0"
            else:
                assert (
                    mcu_files[expected_name]["type"] == "file"
                ), f"File {expected_name} is not a file"
                # check if the file size is the same
                assert (
                    item.stat().st_size == mcu_files[expected_name]["size"]
                ), f"File {expected_name} size is different"

        # create a return folder and copy the file back
        return_folder = tmp_path / "return"
        return_folder.mkdir(exist_ok=True)
        r = board.run_command(f"cp -r :{folder_name} {return_folder.as_posix()}")
        assert r[0] == 0

        # check if all the files have been copied and have the same content
        return_files = list((return_folder / folder_name).rglob("*"))
        assert len(src_content) == len(return_files)
        for item, return_file in zip(src_content, return_files):
            if item.is_dir():
                assert return_file.is_dir()
            else:
                assert item.read_bytes() == return_file.read_bytes()

    finally:
        try:
            wipe_filesystem(board.serialport, f"{dest_folder}/{folder_name}")
        except Exception as e:
            print(e)
        pass
