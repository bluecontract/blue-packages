from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
def test_final_gas_reference_and_conformance_vectors():
    subprocess.run([sys.executable,str(ROOT/'tests/final_gas_runner.py'),str(ROOT/'conformance/bex.json')],check=True)
