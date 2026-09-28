import shutil


def is_binary_available(binary_name: str) -> bool:
    """Checks if a media player binary exists in the system PATH."""
    return shutil.which(binary_name) is not None
