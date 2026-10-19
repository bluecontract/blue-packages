from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools'))
from verify_runtime import verify_current_runtime
verify_current_runtime()
