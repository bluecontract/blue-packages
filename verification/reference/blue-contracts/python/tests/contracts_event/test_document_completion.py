"""Independent completion-1 oracles, derived from C17/C18 and A01–A11.

The first four tests were run against the unmodified event-1 baseline; their
failures are retained in runs/codex/contracts-completion-1/baseline-tests.log.
"""
import unittest
from copy import deepcopy
from pathlib import Path

from blue_contracts import Processor
from vendor import yaml
from .test_contracts_event_api import T, change, update, flow, operation

EXAMPLES = Path(__file__).resolve().parents[2] / 'inputs/contracts-completion-1-design/examples'


class DocumentCompletion(unittest.TestCase):
    def setUp(self):
        self.p = Processor()

    def example(self):
        return yaml.safe_load((EXAMPLES / '01-parent.yaml').read_text())

    def run_example(self, document=None):
        initial = self.p.create(document if document is not None else self.example())
        result = self.p.process(initial, T('Operation Request', channel='input', operation='start'), 1000000)
        self.assertEqual(result.status, 'APPLIED', result.diagnostic)
        return result

    def test_dc01_updates_are_local_and_state_only_completion_is_installed(self):
        document = self.example()
        child = document['b']
        child['seen'] = []
        child['contracts']['start']['steps'] = [update(change('/count', 1), change('/count', 2))]
        child['contracts']['updates'] = T('Document Update Channel', path='/count')
        child['contracts']['observe'] = flow(update(change('/seen/-', {'$document': '/count'}, 'add')), channel='updates')
        result = self.run_example(document)
        self.assertEqual(self.p.read(result.snapshot, '/b/seen'), [1, 2])
        self.assertEqual(self.p.read(result.snapshot, '/b/count'), 2)
        self.assertFalse(self.p.read(result.snapshot, '/deepUpdateSeen'))
        self.assertEqual(self.p.emitted(result), [])

    def test_dc05_parent_reads_completed_child_not_emission_time_state(self):
        result = self.run_example()
        self.assertEqual(self.p.read(result.snapshot, '/payloadAtE1'), 1)
        self.assertEqual(self.p.read(result.snapshot, '/childAtE1'), 2)
        self.assertTrue(self.p.read(result.snapshot, '/b/handledE2'))

    def test_dc06_complete_child_batch_precedes_parent_local_emissions(self):
        result = self.run_example()
        self.assertEqual(self.p.read(result.snapshot, '/stageAtP1'), 2)
        self.assertEqual(self.p.emitted(result), [{'kind': 'P1'}])

    def test_dc11_retiring_occurrence_cannot_interrupt_completed_source(self):
        document = self.example()
        document['contracts']['observeE1']['steps'].append(update(change('/b', None, 'remove')))
        result = self.run_example(document)
        self.assertEqual(self.p.read(result.snapshot, '/stage'), 0)
        child_keys = [key for key in result.snapshot.documents if key != result.snapshot.root]
        self.assertEqual(len(child_keys), 1)
        self.assertTrue(self.p.read(result.snapshot, '/handledE2', document=child_keys[0]))


if __name__ == '__main__':
    unittest.main()
