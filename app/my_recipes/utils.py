import os
import shutil
from uuid import uuid4
from werkzeug.utils import secure_filename

def save_temp_file(file, upload_folder, subfolder = 'image/recipes/tmp'):
    os.makedirs(os.path.join(upload_folder,subfolder), exist_ok = True)
    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique = f"{uuid4().hex}.{ext}" if ext else uuid4().hex
    dest = os.path.join(upload_folder, subfolder, unique)
    file.save(dest)
    return os.path.join(subfolder, unique).replace('\\','/')

def temp_to_permanent(upload_folder, temp_relpath, permanent_subfolder = 'image/recipes'):
    if not temp_relpath:
        return None
    temp_path = os.path.join(upload_folder, temp_relpath)
    if not os.path.exists(temp_path):
        return None
    os.makedirs(os.path.join(upload_folder, permanent_subfolder), exist_ok = True)
    basename = os.path.basename(temp_path)
    dest_rel = os.path.join(permanent_subfolder, basename).replace('\\','/')
    dest_abs = os.path.join(upload_folder, dest_rel)
    shutil.move(temp_path, dest_abs)
    return dest_rel

def delete_file(upload_folder, relpath):
    if not relpath:
        return
    path = os.path.join(upload_folder, relpath)
    if os.path.exists(path):
        os.remove(path)
