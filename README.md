# AFWRename

A cross-platform desktop application built with Python and PySide6 to visually select and rename groups of images.

## Features

-   **Visual Image Selection**: Select images using a file picker or by dragging and dropping them into the app.
-   **Thumbnail Previews**: View selected images in a grid.
-   **Set Grouping**: Group images into sets of 1, 2, or 3.
-   **Automated Renaming**: Files are renamed based on a structured format (e.g., `set2-no1 (1).jpg`).
-   **Flexible Output**: Rename files directly (in-place) or copy them to a new folder.
-   **Undo/Reset**: Easily undo the last set assignment or reset all selections.

## Tech Stack

-   **Language**: Python 3.10+
-   **GUI Framework**: PySide6
-   **Image Handling**: Pillow
-   **Packaging**: PyInstaller

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd image-renamer
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python main.py
    ```

## How to Package

PyInstaller can be used to create a standalone executable for Windows or Linux.

1.  **Install PyInstaller:**
    ```bash
    pip install pyinstaller
    ```

2.  **Package the application:**
    
    For Windows (.exe):
    ```bash
    pyinstaller --onefile --windowed --name ImageRenamer main.py
    ```

    For Linux:
    ```bash
    pyinstaller --onefile --windowed --name ImageRenamer main.py
    ```
The executable will be located in the `dist` directory.