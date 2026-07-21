"""Prompt library — versioned, composable prompts for hero artwork."""

from .library import PromptLibrary, PromptVariant, load_library

# Load the default library on import
_library = None

def get_library() -> PromptLibrary:
    global _library
    if _library is None:
        _library = load_library()
    return _library
