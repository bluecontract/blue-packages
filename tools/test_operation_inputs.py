"""Native authoring conformance. Requires the same qualified classpath as package publication."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OperationInputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classpath = os.environ.get('BLUE_JAVA_CLASSPATH')
        if not cls.classpath:
            raise RuntimeError('Set BLUE_JAVA_CLASSPATH to the qualified native runtime classpath')
        home = os.environ.get('JAVA_HOME')
        cls.java = str(Path(home) / 'bin/java') if home else 'java'
        javac = str(Path(home) / 'bin/javac') if home else 'javac'
        cls.temporary = tempfile.TemporaryDirectory(prefix='operation-input-tests-')
        cls.addClassCleanup(cls.temporary.cleanup)
        subprocess.run([javac, '-cp', cls.classpath, '-d', cls.temporary.name,
                        *[str(ROOT / 'tools' / name) for name in
                          ['QualificationRuntime.java', 'OperationInputs.java', 'BuildPaymentFamily.java',
                           'BuildFinalGas.java', 'OperationInputConformance.java']]], check=True)

    def run_native(self, mode):
        result = subprocess.run([self.java, '-Xmx1500m', '-cp', self.temporary.name + os.pathsep + self.classpath,
                                 'OperationInputConformance', mode, str(ROOT)], capture_output=True, text=True)
        print(result.stdout, end='')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_input_semantics(self):
        self.run_native('native')

    def test_payment_builder(self):
        self.run_native('payment')

    def test_final_gas_builder(self):
        self.run_native('final')


if __name__ == '__main__':
    unittest.main()
