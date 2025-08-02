# AFWRename/core/set_manager.py

from collections import deque

class SetManager:
    """Manages the logic of creating and handling image sets."""

    def __init__(self):
        self.sets = {}
        self.history = deque()
        self._counters = {'set1': 0, 'set2': 0, 'set3': 0}

    def add_set(self, set_size: int, image_paths: list[str]):
        """
        Adds a new set of images.

        Args:
            set_size (int): The number of images in this set type (1, 2, or 3).
            image_paths (list[str]): The list of image file paths from the primary folder.
        """
        if not image_paths:
            return None
        
        # For sets of 2 or 3, we must have the exact number of images.
        if set_size > 1 and len(image_paths) != set_size:
            return None

        key_prefix = f"set{set_size}"
        if set_size > 1:
            self._counters[key_prefix] += 1
            set_name = f"{key_prefix}-no{self._counters[key_prefix]}"
            self.sets[set_name] = image_paths
        else: # set1 case
            # For set1, we can add multiple images/groups to the same set name.
            set_name = key_prefix
            if set_name not in self.sets:
                self.sets[set_name] = []
            self.sets[set_name].extend(image_paths)

        history_entry = (set_name, image_paths)
        self.history.append(history_entry)
        return set_name

    def undo_last_set(self):
        """Removes the last added set."""
        if not self.history:
            return None

        last_set_name, last_images = self.history.pop()

        if "no" in last_set_name:
            prefix = last_set_name.split('-')[0]
            self._counters[prefix] -= 1
            del self.sets[last_set_name]
        else: # set1 case
            # Remove only the specific images that were last added
            self.sets[last_set_name] = [
                img for img in self.sets[last_set_name] if img not in last_images
            ]
            if not self.sets[last_set_name]:
                del self.sets[last_set_name]
        
        return last_images

    def get_all_sets(self):
        """Returns the dictionary of all current sets."""
        return self.sets

    def reset(self):
        """Clears all sets and resets counters."""
        self.sets.clear()
        self.history.clear()
        self._counters = {'set1': 0, 'set2': 0, 'set3': 0}