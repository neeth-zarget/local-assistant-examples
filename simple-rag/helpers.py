import os

from config import Config

def get_sys_dirs_array():
    return [Config.BOOKS_DIR, Config.BOOKS_PROCESSED_DIR]

def create_data_sub_dirs_if_not_exists():
    dirs = get_sys_dirs_array()
    for dir in dirs:
        if not os.path.exists(dir):
            os.makedirs(dir)

def get_processed_file_name(file_path: str) -> str:
    base_name = os.path.basename(file_path)
    name, ext = os.path.splitext(base_name)
    if ext == ".epub":
        return f"{name}.txt"
    return base_name