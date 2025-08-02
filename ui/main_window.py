# AFWRename/ui/main_window.py

import sys
from pathlib import Path

from PIL import Image
Image.MAX_IMAGE_PIXELS = None 

import fitz  # PyMuPDF

from PySide6.QtCore import Qt, QSize, QThread, QObject, Signal
from PySide6.QtGui import QIcon, QPixmap, QShortcut, QKeySequence, QImage
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QGroupBox, QHBoxLayout, QFileDialog,
    QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QPushButton,
    QRadioButton, QVBoxLayout, QWidget, QLabel
)

from core.set_manager import SetManager
from core.renamer import rename_files


class ThumbnailWorker(QObject):
    thumbnail_ready = Signal(str, str, QPixmap)
    finished = Signal()
    file_skipped = Signal(str, str)

    def __init__(self, paths_to_load: list[str], icon_size: QSize):
        super().__init__()
        self.paths_to_load = paths_to_load
        self.thumbnail_size = (256, 256)
        self.is_running = True

    def run(self):
        """The main work of the thread. Handles both images and PDFs."""
        for path_str in self.paths_to_load:
            if not self.is_running:
                break
            
            path = Path(path_str)
            pixmap = None

            try:
                if path.suffix.lower() == ".pdf":
                    with fitz.open(path) as doc:
                        if len(doc) > 0:
                            # --- YOUR CORRECT FIX IS APPLIED HERE ---
                            page = doc.load_page(0)  # type: ignore[attr-defined]
                            fitz_pix = page.get_pixmap()
                            q_image = QImage(fitz_pix.samples, fitz_pix.width, fitz_pix.height, fitz_pix.stride, QImage.Format.Format_RGB888)
                            pixmap = QPixmap.fromImage(q_image)
                else:
                    with Image.open(path) as img:
                        img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                        img = img.convert("RGBA")
                        q_image = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format.Format_RGBA8888)
                        pixmap = QPixmap.fromImage(q_image)

                if pixmap and not pixmap.isNull():
                    self.thumbnail_ready.emit(path_str, path.name, pixmap)
                else:
                    self.file_skipped.emit(path_str, "Could not generate a valid thumbnail.")

            except Exception as e:
                self.file_skipped.emit(path_str, f"Could not process file: {e}")
                continue
        
        self.finished.emit()

    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFWRename")
        self.setGeometry(100, 100, 1200, 800)

        self.set_manager = SetManager()
        self.primary_folder = None
        self.synced_folders = []
        self.all_image_paths = []
        self.thumbnail_thread = None
        self.thumbnail_worker = None
        self.thumbnail_cache = {}
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        folder_selection_layout = QHBoxLayout()
        self.select_primary_btn = QPushButton("1. Select Primary Folder")
        self.select_primary_btn.clicked.connect(self.select_primary_folder)
        folder_selection_layout.addWidget(self.select_primary_btn)

        self.select_synced_btn = QPushButton("2. Add Synced Folder(s)")
        self.select_synced_btn.clicked.connect(self.select_synced_folders)
        folder_selection_layout.addWidget(self.select_synced_btn)

        self.clear_folders_btn = QPushButton("Clear All Folders")
        self.clear_folders_btn.clicked.connect(self.clear_folders)
        folder_selection_layout.addWidget(self.clear_folders_btn)

        main_layout.addLayout(folder_selection_layout)

        self.folder_list_label = QLabel("<b>Status:</b> Please select a primary folder to begin.")
        self.folder_list_label.setWordWrap(True)
        main_layout.addWidget(self.folder_list_label)

        self.image_grid = QListWidget()
        self.image_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_grid.setIconSize(QSize(128, 128))
        self.image_grid.setGridSize(QSize(150, 150))
        self.image_grid.setWordWrap(True)
        main_layout.addWidget(self.image_grid)
        self.image_grid.setAcceptDrops(False)

        self.statusBar().showMessage("Ready")
        bottom_layout = QHBoxLayout()
        assignment_group = QGroupBox("Set Assignment")
        assignment_layout = QVBoxLayout(assignment_group)
        self.assign_set1_btn = QPushButton("Assign to Set of 1 [Ctrl+1]")
        self.assign_set2_btn = QPushButton("Assign to Set of 2 [Ctrl+2]")
        self.assign_set3_btn = QPushButton("Assign to Set of 3 [Ctrl+3]")
        self.assign_set1_btn.clicked.connect(lambda: self.assign_to_set(1))
        self.assign_set2_btn.clicked.connect(lambda: self.assign_to_set(2))
        self.assign_set3_btn.clicked.connect(lambda: self.assign_to_set(3))
        self.undo_btn = QPushButton("Undo Last Set [Ctrl+Z]")
        self.undo_btn.setObjectName("undo_btn")
        self.undo_btn.clicked.connect(self.undo_last)
        self.reset_btn = QPushButton("Reset All")
        self.reset_btn.setObjectName("reset_btn")
        self.reset_btn.clicked.connect(self.reset_all)
        assignment_layout.addWidget(self.assign_set1_btn)
        assignment_layout.addWidget(self.assign_set2_btn)
        assignment_layout.addWidget(self.assign_set3_btn)
        assignment_layout.addStretch()
        assignment_layout.addWidget(self.undo_btn)
        assignment_layout.addWidget(self.reset_btn)
        bottom_layout.addWidget(assignment_group)
        
        preview_group = QGroupBox("Set Preview")
        preview_layout = QVBoxLayout(preview_group)
        self.set_preview_list = QListWidget()
        preview_layout.addWidget(self.set_preview_list)
        bottom_layout.addWidget(preview_group)
        
        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        self.rename_inplace_radio = QRadioButton("Rename In-Place")
        self.rename_inplace_radio.setChecked(True)
        self.export_folder_radio = QRadioButton("Export to Folder")
        self.process_btn = QPushButton("Process and Rename")
        self.process_btn.setObjectName("process_btn")
        self.process_btn.clicked.connect(self.process_files)
        output_layout.addWidget(self.rename_inplace_radio)
        output_layout.addWidget(self.export_folder_radio)
        output_layout.addStretch()
        output_layout.addWidget(self.process_btn)
        bottom_layout.addWidget(output_group)
        
        main_layout.addLayout(bottom_layout)
        self.setup_shortcuts()
        self.update_folder_ui_state()

    def select_primary_folder(self):
        self.clear_folders()
        primary = QFileDialog.getExistingDirectory(self, "Select PRIMARY Folder for Thumbnails")
        if primary:
            self.primary_folder = Path(primary)
            self.update_folder_ui_state()
            self.load_images_from_primary()

    def select_synced_folders(self):
        folders_added = 0
        while True:
            synced_folder = QFileDialog.getExistingDirectory(self, "Add a Synced Folder")
            if synced_folder:
                folder_path = Path(synced_folder)
                if folder_path != self.primary_folder and folder_path not in self.synced_folders:
                    self.synced_folders.append(folder_path)
                    folders_added += 1
                else:
                    QMessageBox.warning(self, "Duplicate Folder", "That folder is already in use.")
                reply = QMessageBox.question(self, "Add Another Folder?", "Folder added. Do you want to add another?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    break
            else:
                break
        if folders_added > 0:
            self.update_folder_ui_state()
            
    def clear_folders(self):
        self.primary_folder = None
        self.synced_folders.clear()
        self.all_image_paths.clear()
        self.thumbnail_cache.clear()
        self.image_grid.clear()
        self.set_manager.reset()
        self.update_set_preview()
        self.update_folder_ui_state()

    def update_folder_ui_state(self):
        has_primary = self.primary_folder is not None
        self.select_synced_btn.setEnabled(has_primary)
        self.clear_folders_btn.setEnabled(has_primary)
        self.export_folder_radio.setEnabled(not self.synced_folders)
        if self.synced_folders:
            self.rename_inplace_radio.setChecked(True)
        if not self.primary_folder:
            self.folder_list_label.setText("<b>Status:</b> Please select a primary folder to begin.")
            return
        html = f"<b>Primary:</b> {self.primary_folder.name}<br>"
        if self.synced_folders:
            synced_names = ", ".join([f.name for f in self.synced_folders])
            html += f"<b>Synced:</b> {synced_names}"
        else:
            html += "<b>Synced:</b> None"
        self.folder_list_label.setText(html)

    def load_images_from_primary(self):
        if not self.primary_folder: return
        image_paths = sorted([str(f) for f in self.primary_folder.iterdir() if self.is_supported_file(f)])
        self.all_image_paths = image_paths
        self.load_images_async(self.all_image_paths)
    
    def load_images_async(self, image_paths: list[str]):
        if not image_paths: return
        self.select_primary_btn.setEnabled(False)
        self.select_synced_btn.setEnabled(False)
        self.clear_folders_btn.setEnabled(False)
        self.statusBar().showMessage(f"Loading {len(image_paths)} files...")
        self.thumbnail_thread = QThread()
        self.thumbnail_worker = ThumbnailWorker(image_paths, self.image_grid.iconSize())
        self.thumbnail_worker.moveToThread(self.thumbnail_thread)
        self.thumbnail_thread.started.connect(self.thumbnail_worker.run)
        self.thumbnail_worker.finished.connect(self.thumbnail_thread.quit)
        self.thumbnail_worker.finished.connect(self.thumbnail_worker.deleteLater)
        self.thumbnail_thread.finished.connect(self.thumbnail_thread.deleteLater)
        self.thumbnail_worker.thumbnail_ready.connect(self.add_thumbnail_to_grid)
        self.thumbnail_worker.file_skipped.connect(self.on_file_skipped)
        self.thumbnail_thread.finished.connect(lambda: self.select_primary_btn.setEnabled(True))
        self.thumbnail_thread.finished.connect(lambda: self.update_folder_ui_state())
        self.thumbnail_thread.finished.connect(lambda: self.statusBar().showMessage("Ready", 3000))
        self.thumbnail_thread.start()

    def process_files(self):
        if not self.primary_folder:
            QMessageBox.warning(self, "Warning", "No primary folder selected.")
            return
        sets = self.set_manager.get_all_sets()
        if not sets:
            QMessageBox.information(self, "Information", "No sets to process.")
            return
        output_dir = None
        if not self.synced_folders and self.export_folder_radio.isChecked():
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if not output_dir: return
        try:
            renamed_files = rename_files(sets, self.primary_folder, self.synced_folders, output_dir)
            QMessageBox.information(self, "Success", f"Successfully processed {len(renamed_files)} files.")
            self.clear_folders()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during processing:\n{e}")

    def reset_all(self):
        if not self.primary_folder: return
        reply = QMessageBox.question(self, "Confirm Reset", "Clear all sets and selections?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.set_manager.reset()
            self.update_set_preview()
            self.image_grid.clear()
            self.load_images_async(self.all_image_paths)
            
    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self.assign_to_set(1))
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self.assign_to_set(2))
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self.assign_to_set(3))
        QShortcut(QKeySequence.StandardKey.Undo, self).activated.connect(self.undo_last)
        
    def on_file_skipped(self, path, reason):
        self.statusBar().showMessage(f"Skipped {Path(path).name}: {reason}", 5000)
        
    def add_thumbnail_to_grid(self, path_str, name, pixmap):
        self.thumbnail_cache[path_str] = pixmap
        item = QListWidgetItem(QIcon(pixmap), name)
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        self.image_grid.addItem(item)
        
    def assign_to_set(self, set_size: int):
        selected_items = self.image_grid.selectedItems()
        if not selected_items: return
        if set_size > 1 and len(selected_items) != set_size:
            QMessageBox.warning(self, "Warning", f"You must select exactly {set_size} files.")
            return
        image_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        if self.set_manager.add_set(set_size, image_paths):
            for item in selected_items:
                self.image_grid.takeItem(self.image_grid.row(item))
            self.update_set_preview()
            
    def undo_last(self):
        undone_images = self.set_manager.undo_last_set()
        if not undone_images: return
        all_visible_paths = {self.image_grid.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.image_grid.count())}
        all_visible_paths.update(undone_images)
        sorted_paths = [p for p in self.all_image_paths if p in all_visible_paths]
        self.image_grid.setUpdatesEnabled(False)
        self.image_grid.clear()
        for path_str in sorted_paths:
            pixmap = self.thumbnail_cache.get(path_str)
            if pixmap: self.add_thumbnail_to_grid(path_str, Path(path_str).name, pixmap)
        self.image_grid.setUpdatesEnabled(True)
        self.update_set_preview()
        for i in range(self.image_grid.count()):
            item = self.image_grid.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in undone_images:
                item.setSelected(True)
        self.image_grid.setFocus()
        
    def is_supported_file(self, path: Path):
        """Checks if the file is a supported image or a PDF."""
        return path.is_file() and path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".pdf"]
        
    def update_set_preview(self):
        self.set_preview_list.clear()
        sets = self.set_manager.get_all_sets()
        for set_name in sorted(sets.keys()):
            images = sets[set_name]
            if set_name.startswith("set1"):
                display_text = f"Set 1: {len(images)} files"
                existing_items = self.set_preview_list.findItems("Set 1:", Qt.MatchFlag.MatchStartsWith)
                if not existing_items: self.set_preview_list.addItem(display_text)
                else: existing_items[0].setText(display_text)
            else:
                self.set_preview_list.addItem(f"{set_name}: {len(images)} files")