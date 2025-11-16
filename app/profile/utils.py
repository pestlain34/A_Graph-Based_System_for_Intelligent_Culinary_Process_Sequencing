import os


def delete_file(upload_folder, relpath):
    if not relpath:
        return
    path = os.path.join(upload_folder, relpath)
    if os.path.exists(path):
        os.remove(path)
