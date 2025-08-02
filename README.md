# AFWRename

A cross-platform desktop application to visually select and rename groups of images, with support for synchronizing renames across multiple folders based on a shared file ID.

## Features

-   **Synced Folder Renaming**: Select a primary folder and multiple synced folders. Renaming an image in the primary folder will automatically apply the same rename to corresponding images in all synced folders.
-   **Unique ID Matching**: Links images across folders by matching a unique number in parentheses within the filename (e.g., `(247)`).
-   **Support for Images and PDFs**: Generates thumbnails for common image formats and the first page of PDF documents.
-   **Visual Image Selection**: View thumbnails from the primary folder in a fast, responsive grid.
-   **Set Grouping**: Group images into sets of 1, 2, or 3.
-   **Keyboard Shortcuts**: Assign sets (`Ctrl+1`, `Ctrl+2`, `Ctrl+3`) and undo (`Ctrl+Z`) for maximum efficiency.
-   **High-Performance**: Uses background threading and efficient thumbnail generation to handle very large image libraries without freezing.

## Tech Stack

-   **Language**: Python 3.10+
-   **GUI Framework**: PySide6
-   **Image Handling**: Pillow
-   **Packaging**: PyInstaller (for Windows `.exe`) and appimage-builder (for Linux `.AppImage`)

## How to Run

1.  **Clone the repository.**
2.  **Create and activate a virtual environment** using a stable Python version (e.g., 3.10 or 3.11):
    ```bash
    python3.11 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Run the application:**
    ```bash
    python main.py