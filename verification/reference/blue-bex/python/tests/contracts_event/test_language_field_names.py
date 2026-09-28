"""Public processor control for the independent Language representation repair."""
import unittest
from blue_contracts import Processor


class LanguageFieldNames(unittest.TestCase):
    def test_mutation_and_read_of_n_native_metadata_charge(self):
        def typed(name, **fields): return {'type': 'Contracts/' + name, **fields}
        processor = Processor()
        state = processor.create({'n': {'child': [1, 2]}, 'contracts': {
            'input': typed('External Channel'),
            'go': typed('Sequential Workflow Operation', channel='input', steps=[typed(
                'Update Document', changeset=[{'op': 'replace', 'path': '/n/child/0', 'val': 3}])])}})
        event = typed('Operation Request', channel='input', operation='go')
        result = processor.process(state, event, 10)
        self.assertEqual(result.status, 'APPLIED')
        # Local Language revision: specification is no longer an inherited field.
        # Original 583/582 control is preserved in provenance and paired trace evidence.
        # Rates are unchanged; recomputed logical work is 581, with rollback at 580.
        self.assertEqual(result.gas, 581)
        self.assertEqual(processor.read(result.snapshot, '/n'), {'child': [3, 2]})
        processor.gas_limit = 580
        rejected = processor.process(state, event, 10)
        self.assertEqual(rejected.status, 'GAS_LIMIT_EXCEEDED')
        self.assertEqual(rejected.snapshot.identity, state.identity)
        self.assertEqual(processor.read(rejected.snapshot, '/n'), {'child': [1, 2]})
