"""Distribution adapter selecting the bundled, hash-locked reference."""
from pathlib import Path
import hashlib,json,os,sys
ROOT=Path(__file__).resolve().parents[1]
WORKSPACE=ROOT.parent/'verification/reference/blue-language'
# Original package processor expects this directory name.
if sys.version_info < (3,13): raise RuntimeError("Python 3.13 or newer is required")
SOURCE_LOCK=json.loads((WORKSPACE/"SOURCE-LOCK.json").read_text())
LOCK={"blue":{"archiveSha256":SOURCE_LOCK["sourceArchiveSha256"],"files":SOURCE_LOCK["files"]}}
sys.dont_write_bytecode=True
sys.path.insert(0,str(WORKSPACE/"python"/"src"))
