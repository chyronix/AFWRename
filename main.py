# image-renamer/main.py
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Define the color palette from the tokens
COLORS = {
    "brand-bg": "#0B0F19",
    "brand-fg": "#F8FAFC",
    "brand-card": "#121826",
    "brand-popover": "#080B14",
    "brand-primary": "#F05192",
    "brand-primary-fg": "#FFF2F6",
    "brand-secondary": "#1E293B",
    "brand-muted-fg": "#64748B",
    "brand-destructive": "#792121",
    "brand-input": "#273349",
}

# Define the Qt StyleSheet (QSS)
STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {COLORS["brand-bg"]};
        color: {COLORS["brand-fg"]};
        font-family: "Segoe UI", "Roboto", "Helvetica Neue", "Arial", sans-serif;
    }}
    QGroupBox {{
        background-color: {COLORS["brand-card"]};
        border: 1px solid {COLORS["brand-secondary"]};
        border-radius: 6px;
        margin-top: 12px;
        font-weight: bold;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 5px 0 5px;
        color: {COLORS["brand-muted-fg"]};
    }}
    QListWidget {{
        background-color: {COLORS["brand-card"]};
        border: 1px solid {COLORS["brand-secondary"]};
        border-radius: 6px;
        padding: 5px;
    }}
    QListWidget::item {{
        color: {COLORS["brand-fg"]};
        padding: 5px;
        border-radius: 3px; /* For selection highlight */
    }}
    QListWidget::item:selected {{
        background-color: {COLORS["brand-primary"]};
        color: {COLORS["brand-primary-fg"]};
        border: none;
    }}
    QPushButton {{
        background-color: {COLORS["brand-secondary"]};
        color: {COLORS["brand-fg"]};
        border: none;
        padding: 10px 15px;
        border-radius: 6px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLORS["brand-muted-fg"]};
    }}
    QPushButton:pressed {{
        background-color: {COLORS["brand-input"]};
    }}
    /* Primary Action Button */
    QPushButton#process_btn {{
        background-color: {COLORS["brand-primary"]};
        color: {COLORS["brand-primary-fg"]};
    }}
    QPushButton#process_btn:hover {{
        background-color: #D84884; /* A slightly darker shade for hover */
    }}
    /* Destructive Action Buttons */
    QPushButton#undo_btn, QPushButton#reset_btn {{
        background-color: {COLORS["brand-destructive"]};
        color: {COLORS["brand-fg"]};
    }}
    QPushButton#undo_btn:hover, QPushButton#reset_btn:hover {{
        background-color: #9C2C2C; /* A slightly darker shade for hover */
    }}
    QRadioButton {{
        color: {COLORS["brand-fg"]};
        padding: 5px;
    }}
    QRadioButton::indicator::unchecked {{
        border: 2px solid {COLORS["brand-secondary"]};
        background-color: {COLORS["brand-card"]};
        border-radius: 7px;
        width: 14px;
        height: 14px;
    }}
    QRadioButton::indicator::checked {{
        border: 2px solid {COLORS["brand-primary"]};
        background-color: {COLORS["brand-primary"]};
        border-radius: 7px;
        width: 14px;
        height: 14px;
    }}
    QMessageBox {{
        background-color: {COLORS["brand-popover"]};
    }}
    QScrollBar:vertical {{
        background: {COLORS["brand-card"]};
        width: 12px;
        margin: 0px 0px 0px 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS["brand-secondary"]};
        min-height: 20px;
        border-radius: 6px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLORS["brand-muted-fg"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)  # Apply the stylesheet
    window = MainWindow()
    window.show()
    sys.exit(app.exec())