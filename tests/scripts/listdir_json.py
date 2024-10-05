# %%micropython

import os


# %%micropython

import os


def listdir(path=".", sub=False, JSON=True, hash=False):
    # RETURNS the file information of a folder as a dictionary
    # optionally returns the information as a JSON string
    if hash:
        import hashlib, binascii
    if JSON:
        import json

    file_dict = {}
    if path == ".":  # Get current folder name
        path = os.getcwd()
    # print("+listdir:{}".format(path))
    try:
        files = os.listdir(path)
    except Exception:
        files = []
    for file in files:
        # get size of each file
        info = {"path": path, "Name": file, "size": 0}
        if path and path[-1] == "/":
            full = "%s%s" % (path, file)
        else:
            full = "%s/%s" % (path, file)
        # print("os.stat({})".format( full))
        subdir = {}
        try:
            stat = os.stat(full)
            if stat[0] & 0x4000:  # stat.S_IFDIR
                info["type"] = "dir"
                # recurse folder(s)
                if sub == True:
                    # print("Folder :{}".format( full))
                    subdir = listdir(path=full, sub=True, JSON=False, hash=hash)
            else:
                info["size"] = stat[6]
                info["type"] = "file"
                if hash:
                    with open(full, "rb") as f:
                        h = hashlib.sha256(f.read())
                        info["hash"] = binascii.hexlify(h.digest())
        except OSError as e:
            # print("error:{} processing file:{}".format(e, full))
            info["error"] = e.args[0]
            info["type"] = "OSError"
        # info["fullname"] = full
        file_dict[full] = info
        # recurse folder(s)
        if sub == True:
            file_dict.update(subdir)  # type: ignore
    if JSON == True:
        return json.dumps(file_dict)
    else:
        return file_dict
