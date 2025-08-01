# image-renamer/ui/main_window.py

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QThread, QObject, Signal
from PySide6.QtGui import QIcon, QPixmap, QShortcut, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.set_manager import SetManager
from core.renamer import rename_files


class ThumbnailWorker(QObject):
    thumbnail_ready = Signal(str, str, QPixmap)
    finished = Signal()

    def __init__(self, paths_to_load: list[str], icon_size: QSize):
        super().__init__()
        self.paths_to_load = paths_to_load
        self.icon_size = icon_size
        self.is_running = True

    def run(self):
        for path_str in self.paths_to_load:
            if not self.is_running: break
            path = Path(path_str)
            pixmap = QPixmap(str(path))
            scaled_pixmap = pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.thumbnail_ready.emit(path_str, path.name, scaled_pixmap)
        self.finished.emit()

    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AFWRename")
        self.setGeometry(100, 100, 1200, 800)

        self.set_manager = SetManager()
        self.all_image_paths = []
        self.thumbnail_thread = None
        self.thumbnail_worker = None
        self.thumbnail_cache = {}

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.select_images_btn = QPushButton("Select Images")
        self.select_images_btn.clicked.connect(self.select_images)
        main_layout.addWidget(self.select_images_btn)
        
        self.image_grid = QListWidget()
        self.image_grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.image_grid.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.image_grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.image_grid.setIconSize(QSize(128, 128))
        self.image_grid.setGridSize(QSize(150, 150))
        self.image_grid.setWordWrap(True)
        main_layout.addWidget(self.image_grid)
        self.image_grid.setAcceptDrops(True)
        self.image_grid.dragEnterEvent = self.dragEnterEvent
        self.image_grid.dropEvent = self.dropEvent
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
    
    def setup_shortcuts(self):
        shortcut_set1 = QShortcut(QKeySequence("Ctrl+1"), self)
        shortcut_set2 = QShortcut(QKeySequence("Ctrl+2"), self)
        shortcut_set3 = QShortcut(QKeySequence("Ctrl+3"), self)
        shortcut_set1.activated.connect(lambda: self.assign_to_set(1))
        shortcut_set2.activated.connect(lambda: self.assign_to_set(2))
        shortcut_set3.activated.connect(lambda: self.assign_to_set(3))
        shortcut_undo = QShortcut(QKeySequence.StandardKey.Undo, self)
        shortcut_undo.activated.connect(self.undo_last)
        
    # --- THIS IS THE MISSING METHOD ---
    def select_images(self):
        """Opens a file dialog to select images and loads them."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", "", "Image Files (*.png *.jpg *.jpeg *.webp)"
        )
        if files:
            self.load_images(files)
    # --- END OF MISSING METHOD ---

    def load_images(self, image_paths: list[str]):
        new_paths = [p for p in image_paths if p not in self.all_image_paths]
        if not new_paths: return

        self.all_image_paths.extend(new_paths)
        self.select_images_btn.setEnabled(False)
        self.statusBar().showMessage(f"Loading {len(new_paths)} images...")

        self.thumbnail_thread = QThread()
        self.thumbnail_worker = ThumbnailWorker(new_paths, self.image_grid.iconSize())
        self.thumbnail_worker.moveToThread(self.thumbnail_thread)
        self.thumbnail_thread.started.connect(self.thumbnail_worker.run)
        self.thumbnail_worker.finished.connect(self.thumbnail_thread.quit)
        self.thumbnail_worker.finished.connect(self.thumbnail_worker.deleteLater)
        self.thumbnail_thread.finished.connect(self.thumbnail_thread.deleteLater)
        self.thumbnail_worker.thumbnail_ready.connect(self.add_thumbnail_to_grid)
        self.thumbnail_thread.finished.connect(lambda: self.select_images_btn.setEnabled(True))
        self.thumbnail_thread.finished.connect(lambda: self.statusBar().showMessage("Ready", 3000))
        self.thumbnail_thread.start()

    def add_thumbnail_to_grid(self, path_str, name, pixmap):
        self.thumbnail_cache[path_str] = pixmap
        icon = QIcon(pixmap)
        item = QListWidgetItem(icon, name)
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        self.image_grid.addItem(item)

    def assign_to_set(self, set_size: int):
        selected_items = self.image_grid.selectedItems()
        if not selected_items: return
        
        if set_size > 1 and len(selected_items) != set_size:
            QMessageBox.warning(self, "Warning", f"You must select exactly {set_size} images for this set type.")
            return

        image_paths = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        set_name = self.set_manager.add_set(set_size, image_paths)

        if set_name:
            for item in selected_items:
                self.image_grid.takeItem(self.image_grid.row(item))
            self.update_set_preview()

    def undo_last(self):
        undone_images = self.set_manager.undo_last_set()
        if not undone_images: return
        
        all_visible_paths = {self.image_grid.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.image_grid.count())}
        all_visible_paths.update(undone_images)
        sorted_paths_to_display = [p for p in self.all_image_paths if p in all_visible_paths]
        
        self.image_grid.setUpdatesEnabled(False)
        self.image_grid.clear()
        for path_str in sorted_paths_to_display:
            pixmap = self.thumbnail_cache.get(path_str)
            if pixmap:
                icon = QIcon(pixmap)
                item = QListWidgetItem(icon, Path(path_str).name)
                item.setData(Qt.ItemDataRole.UserRole, path_str)
                self.image_grid.addItem(item)
        self.image_grid.setUpdatesEnabled(True)
        self.update_set_preview()

        items_to_select = []
        for i in range(self.image_grid.count()):
            item = self.image_grid.item(i)
            if item.data(Qt.ItemDataRole.UserRole) in undone_images:
                items_to_select.append(item)
        for item in items_to_select:
            item.setSelected(True)
        self.image_grid.setFocus()

    def reset_all(self):
        reply = QMessageBox.question(self, "Confirm Reset", "Are you sure you want to clear all selections and sets?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.set_manager.reset()
            self.update_set_preview()
            self.image_grid.setUpdatesEnabled(False)
            self.image_grid.clear()
            for path_str in self.all_image_paths:
                pixmap = self.thumbnail_cache.get(path_str)
                if pixmap:
                    icon = QIcon(pixmap)
                    item = QListWidgetItem(icon, Path(path_str).name)
                    item.setData(Qt.ItemDataRole.UserRole, path_str)
                    self.image_grid.addItem(item)
            self.image_grid.setUpdatesEnabled(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        image_paths = [str(Path(url.toLocalFile())) for url in urls if self.is_image_file(Path(url.toLocalFile()))]
        self.load_images(image_paths)
    def is_image_file(self, path: Path):
        return path.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]
    def update_set_preview(self):
        self.set_preview_list.clear()
        sets = self.set_manager.get_all_sets()
        for set_name in sorted(sets.keys()):
            images = sets[set_name]
            if set_name.startswith("set1"):
                display_text = f"Set 1: {len(images)} images"
                existing_items = self.set_preview_list.findItems("Set 1:", Qt.MatchFlag.MatchStartsWith)
                if not existing_items: self.set_preview_list.addItem(display_text)
                else: existing_items[0].setText(display_text)
            else:
                display_text = f"{set_name}: {len(images)} images"
                self.set_preview_list.addItem(display_text)
    def process_files(self):
        sets = self.set_manager.get_all_sets()
        if not sets:
            QMessageBox.information(self, "Information", "No sets to process.")
            return
        output_dir = None
        if self.export_folder_radio.isChecked():
            output_dir = QFileDialog.getExistingDirectory(self, "Select Output Folder")
            if not output_dir: return
        try:
            renamed_files = rename_files(sets, output_dir)
            QMessageBox.information(self, "Success", f"Successfully processed {len(renamed_files)} files.")
            self.set_manager.reset()
            if not output_dir:
                path_map = {old: new for old, new in renamed_files}
                self.all_image_paths = [path_map.get(p, p) for p in self.all_image_paths if p not in path_map]
                for old, new in path_map.items():
                    if old in self.thumbnail_cache:
                        self.thumbnail_cache[new] = self.thumbnail_cache.pop(old)
            
            # Use a dummy reset call to trigger the redraw
            self.reset_all()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during processing:\n{e}")