import os


def wipe_folder(path=".", sub=True):
    print("wipe path {}".format(path))
    l = os.listdir(path)
    l.sort()
    # print(l)
    if l != [""]:
        for f in l:
            child = "{}/{}".format(path, f)
            print(" - " + child)
            st = os.stat(child)
            if st[0] & 0x4000:  # stat.S_IFDIR
                if sub:
                    wipe_folder(child, sub)
                    try:
                        os.rmdir(child)
                    except:
                        print("Error deleting folder {}".format(child))
            else:  # File
                try:
                    os.remove(child)
                except:
                    print("Error deleting file {}".format(child))
