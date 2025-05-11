"""
This module contains custom exception types that I have used throughout
my code.
"""

class AssetError(Exception):
    "Asset could not be found."
    def __init__(self, path: str) -> None:
        super().__init__(f"The image path '\033[33m{path}\033[0m' does not exist in the textures folder.")

class AssetLinkError(Exception):
    "There is a problem with the class asset link file."
    def __init__(self, file_path: str, message: str) -> None:
        super().__init__(f"Error found at {file_path}: {message}")

class InitialisationError(Exception):
    "Class initialisation failed."

class SaveFileError(Exception):
    "Save file got corrupted."
    def __init__(self, save_file_name: str) -> None:
        super().__init__(f"The save file being loaded got corrupted: 'data/save_files/{save_file_name}.bin'")