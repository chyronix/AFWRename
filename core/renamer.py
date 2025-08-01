# image-renamer/core/renamer.py
import shutil
from pathlib import Path

def rename_files(sets: dict, output_dir: str = None):
    """
    Renames or copies files based on the provided sets.

    Args:
        sets (dict): The dictionary of sets from SetManager.
        output_dir (str, optional): If provided, copies files to this directory. 
                                    Otherwise, renames them in-place.
    """
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    renamed_files = []

    for set_name, images in sets.items():
        if set_name.startswith("set1"):
             for i, old_path_str in enumerate(images):
                old_path = Path(old_path_str)
                new_name = f"set1 ({i + 1}){old_path.suffix}"
                new_path = output_path / new_name if output_dir else old_path.with_name(new_name)
                
                if output_dir:
                    shutil.copy2(old_path, new_path)
                else:
                    old_path.rename(new_path)
                renamed_files.append((old_path_str, str(new_path)))
        else:
            for i, old_path_str in enumerate(images):
                old_path = Path(old_path_str)
                new_name = f"{set_name} ({i + 1}){old_path.suffix}"
                new_path = output_path / new_name if output_dir else old_path.with_name(new_name)

                if output_dir:
                    shutil.copy2(old_path, new_path)
                else:
                    old_path.rename(new_path)
                renamed_files.append((old_path_str, str(new_path)))
    
    return renamed_files