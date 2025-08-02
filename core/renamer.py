# AFWRename/core/renamer.py

import shutil
from pathlib import Path
import re

# This regex finds a number in parentheses, e.g., "(247)", to use as a unique ID.
ID_PATTERN = re.compile(r'\((\d+)\)\.[a-zA-Z]+$')

def find_file_by_id(folder: Path, image_id: str):
    """Scans a folder to find a file whose name contains the given unique ID."""
    for file_path in folder.iterdir():
        match = ID_PATTERN.search(file_path.name)
        if match and match.group(1) == image_id:
            return file_path
    return None

def rename_files(
    sets: dict,
    primary_folder: Path,
    synced_folders: list[Path],
    output_dir: str | None = None
):
    """
    Renames files based on sets. In sync mode, it uses a unique ID
    extracted from the filename to rename corresponding files across all folders.
    """
    all_target_folders = [primary_folder] + synced_folders
    
    renamed_files_log = []
    set1_counter = 0
    sorted_set_names = sorted(sets.keys())

    for set_name in sorted_set_names:
        primary_image_paths = sets[set_name]
        is_set1 = set_name.startswith("set1")
        
        for i, primary_path_str in enumerate(primary_image_paths):
            old_primary_path = Path(primary_path_str)
            
            match = ID_PATTERN.search(old_primary_path.name)
            if not match:
                print(f"Warning: Could not find a unique ID in '{old_primary_path.name}'. Skipping.")
                continue

            image_id = match.group(1)

            if is_set1:
                set1_counter += 1
                new_base_name = f"set1 ({set1_counter})"
            else:
                new_base_name = f"{set_name} ({i + 1})"

            for folder in all_target_folders:
                file_to_rename = find_file_by_id(folder, image_id)
                
                if file_to_rename and file_to_rename.exists():
                    new_full_name = f"{new_base_name}{file_to_rename.suffix}"
                    new_path = folder / new_full_name
                    file_to_rename.rename(new_path)
                    renamed_files_log.append((str(file_to_rename), str(new_path)))
                else:
                    print(f"Warning: No matching file for ID '({image_id})' found in '{folder.name}'.")

    return renamed_files_log