# image-renamer/ui/main_window.py
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QFileDialog, QListWidget, QListWidgetItem, QAbstractItemView,
                               QMessageBox, QGroupBox, QRadioButton)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize
from pathlib import Path

from core.set_manager import SetManager
from core.renamer import rename_files

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFWRename")
        self.setGeometry(100, 100, 1200, 800)

        self.set_manager = SetManager()
        self.all_image_paths = []

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top controls
        controls_layout = QHBoxLayout()
        self.select_images_btn = QPushButton("Select Images")
        self.select_images_btn.clicked.connect(self.select_images)
        controls_layout.addWidget(self.select_images_btn)
        main_layout.addLayout(controls_layout)

        # Image grid (thumbnail view)
        self.image_grid = QListWidget()
        self.image_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_grid.setGridSize(QSize(150, 150))
        self.image_grid.setIconSize(QSize(128, 128))
        self.image_grid.setWordWrap(True)
        main_layout.addWidget(self.image_grid)
        self.image_grid.setAcceptDrops(True)
        self.image_grid.dragEnterEvent = self.dragEnterEvent
        self.image_grid.dropEvent = self.dropEvent


        # Set assignment and preview
        bottom_layout = QHBoxLayout()
        
        # Assignment buttons
        assignment_group = QGroupBox("Set Assignment")
        assignment_layout = QVBoxLayout(assignment_group)
        
        self.assign_set1_btn = QPushButton("Assign to Set of 1")
        self.assign_set2_btn = QPushButton("Assign to Set of 2")
        self.assign_set3_btn = QPushButton("Assign to Set of 3")
        
        self.assign_set1_btn.clicked.connect(lambda: self.assign_to_set(1))
        self.assign_set2_btn.clicked.connect(lambda: self.assign_to_set(2))
        self.assign_set3_btn.clicked.connect(lambda: self.assign_to_set(3))
        
        self.undo_btn = QPushButton("Undo Last Set")
        self.undo_btn.setObjectName("undo_btn") # Set object name for styling
        self.undo_btn.clicked.connect(self.undo_last)
        
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.setObjectName("reset_btn") # Set object name for styling
        self.reset_btn.clicked.connect(self.reset_all)

        assignment_layout.addWidget(self.assign_set1_btn)
        assignment_layout.addWidget(self.assign_set2_btn)
        assignment_layout.addWidget(self.assign_set3_btn)
        assignment_layout.addStretch() # Add space
        assignment_layout.addWidget(self.undo_btn)
        assignment_layout.addWidget(self.reset_btn)

        bottom_layout.addWidget(assignment_group)

        # Set preview
        preview_group = QGroupBox("Set Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.set_preview_list = QListWidget()
        preview_layout.addWidget(self.set_preview_list)
        bottom_layout.addWidget(preview_group)

        # Output options
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        
        self.rename_inplace_radio = QRadioButton("Rename In-Place")
        self.rename_inplace_radio.setChecked(True)
        
        self.export_folder_radio = QRadioButton("Export to Folder")
        
        self.process_btn = QPushButton("Process and Rename")
        self.process_btn.setObjectName("process_btn") # Set object name for styling
        self.process_btn.clicked.connect(self.process_files)

        output_layout.addWidget(self.rename_inplace_radio)
        output_layout.addWidget(self.export_folder_radio)
        output_layout.addStretch() # Add space
        output_layout.addWidget(self.process_btn)

        bottom_layout.addWidget(output_group)
        main_layout.addLayout(bottom_layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        image_paths = [Path(url.toLocalFile()) for url in urls]
        self.load_images([str(p) for p in image_paths if self.is_image_file(p)])


    def select_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Images",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp)"
        )
        if files:
            self.load_images(files)

    def is_image_file(self, path: Path):
        return path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']

    def load_images(self, image_paths: list[str]):
        new_paths = [p for p in image_paths if p not in self.all_image_paths]
        self.all_image_paths.extend(new_paths)
        for path in new_paths:
            pixmap = QPixmap(path)
            item = QListWidgetItem(QIcon(pixmap), Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.image_grid.addItem(item)
    
    def assign_to_set(self, set_size: int):
        selected_items = self.image_grid.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "No images selected!")
            return
        
        if set_size > 1 and len(selected_items) != set_size:
            QMessageBox.warning(self, "Warning", f"You must select exactly {set_size} images for this set type.")
            return

        image_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        set_name = self.set_manager.add_set(set_size, image_paths)
        if set_name:
            # Remove from grid
            for item in selected_items:
                self.image_grid.takeItem(self.image_grid.row(item))
            self.update_set_preview()

    def update_set_preview(self):
        self.set_preview_list.clear()
        sets = self.set_manager.get_all_sets()
        for set_name, images in sets.items():
            if set_name.startswith("set1"):
                # Consolidate "set1" entries into one line for a cleaner look
                set1_images_count = len(images)
                # Check if an item for set1 already exists
                existing_items = self.set_preview_list.findItems("Set 1:", Qt.MatchFlag.MatchStartsWith)
                if existing_items:
                    existing_items[0].setText(f"Set 1: {set1_images_count} images")
                else:
                    self.set_preview_list.addItem(f"Set 1: {set1_images_count} images")
            else:
                display_text = f"{set_name}: {len(images)} images"
                self.set_preview_list.addItem(display_text)

    def undo_last(self):
        last_images = self.set_manager.undo_last_set()
        if last_images:
            # Add images back to the main grid
            self.load_images(last_images)
            self.update_set_preview()
            
            # Reselect the items for better user experience
            for i in range(self.image_grid.count()):
                item = self.image_grid.item(i)
                if item.data(Qt.ItemDataRole.UserRole) in last_images:
                    item.setSelected(True)


    def reset_all(self):
        reply = QMessageBox.question(self, "Confirm Reset", 
                                     "Are you sure you want to clear all selections and sets?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Store all paths before clearing managers
            all_current_paths = list(self.all_image_paths)

            self.image_grid.clear()
            self.set_preview_list.clear()
            self.set_manager.reset()
            self.all_image_paths.clear()

            # Reload all images from the original list
            self.load_images(all_current_paths)


    def process_files(self):
        sets = self.set_manager.get_all_sets()
        if not sets:
            QMessageBox.information(self, "Information", "No sets to process.")
            return

        output_dir = None
        if self.export_folder_radio.isChecked():
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if not output_dir:
                return # User cancelled

        try:
            renamed_files = rename_files(sets, output_dir)
            
            QMessageBox.information(self, "Success", f"Successfully processed {len(renamed_files)} files.")
            
            # Reset application state after processing
            self.set_preview_list.clear()
            self.set_manager.reset()
            
            # If renaming in place, we need to update the master list of paths
            if not output_dir:
                # Create a map of old paths to new paths
                path_map = {old: new for old, new in renamed_files}
                # Update the master list
                self.all_image_paths = [path_map.get(p, p) for p in self.all_image_paths if p not in path_map]

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during processing:\n{e}")