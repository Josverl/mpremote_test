from mpflash.mpremoteboard import MPRemoteBoard

boards = [MPRemoteBoard(comport) for comport in MPRemoteBoard.connected_boards()]
for board in boards:
    try:
        board.get_mcu_info()
    except Exception as e:
        print(f"Error: {e}")
        boards.remove(board)
