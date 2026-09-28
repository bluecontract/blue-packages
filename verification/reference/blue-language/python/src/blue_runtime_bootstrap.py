"""Locate the supplied Language package, or an explicit compatible checkout."""
from pathlib import Path
import os
import sys

def activate():
    path=Path(os.environ.get('BLUE_LANGUAGE_PATH',Path(__file__).resolve().parent)).resolve()
    if not (path/'blue_language'/'api.py').is_file():
        raise ImportError(f'Blue Language checkout not found at {path}; set BLUE_LANGUAGE_PATH')
    if str(path) not in sys.path:sys.path.insert(0,str(path))
    loaded=sys.modules.get('blue_language')
    if loaded and not str(Path(loaded.__file__).resolve()).startswith(str(path)+os.sep):
        raise ImportError('another Blue Language implementation is already loaded; do not mix policies')
    return path
