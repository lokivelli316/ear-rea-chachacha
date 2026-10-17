"""Regression tests for process boundaries, cancellation and register writers."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ear.adapters import JsonToolAdapter, WordLensAdapter
from ear.engine import Engine
from ear.demo import demonstrate
from ear.register import Register, RegisterError


def append_evidence(args):
    path, number = args
    Register(path).record('evidence', 'sample', {'observation': number})


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'events.jsonl'
        self.reg = Register(self.path)
        self.reg.add_feature('sample', intent='test fixture', source={
            'name': 'WordLens', 'version': '1', 'license': 'original, repository license unselected'},
            strategy='rebuild', adapter='wordlens', evidence='word split semantics', test_plan='count fixture')
        self.reg.decide('sample', approved=True, operator='test')

    def test_concurrent_process_appends_preserve_chain(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
            list(pool.map(append_evidence, [(str(self.path), i) for i in range(12)]))
        events = self.reg.read()
        self.assertEqual(len(events), 14)
        self.assertEqual({e['data']['observation'] for e in events[2:]}, set(range(12)))

    def test_adapter_timeout_is_failure_receipt(self):
        with patch('ear.adapters.subprocess.run', side_effect=subprocess.TimeoutExpired('json.tool', 5)):
            result = JsonToolAdapter().invoke({'document': {}}, {'local:subprocess'})
        self.assertFalse(result['ok'])
        self.assertEqual(result['error']['code'], 'provider_failure')
        self.assertIsNone(result['output'])

    def test_json_nonfinite_input_rejected_before_process(self):
        result = JsonToolAdapter().invoke({'document': {'bad': float('nan')}}, {'local:subprocess'})
        self.assertEqual(result['error']['code'], 'invalid_input')

    def test_unknown_adapter_and_empty_queue(self):
        engine = Engine(self.reg, {})
        result = engine.run({}, execute=True, max_iterations=1)
        self.assertEqual(result['status'], 'limit_reached')
        self.assertEqual(result['iterations'][0]['receipts'][0]['error']['code'], 'unavailable')
        self.assertEqual(engine.run({}, execute=True, feature_ids=[])['status'], 'empty_queue')
        with self.assertRaises(ValueError):
            engine.run({}, feature_ids=['sample', 'sample'])

    def test_provider_exception_becomes_recorded_failure(self):
        class BrokenProvider(WordLensAdapter):
            def invoke(self, inputs, permissions):
                raise RuntimeError('provider broke')
        result = Engine(self.reg, {'wordlens': BrokenProvider()}).run(
            {'text': 'a'}, execute=True, permissions={'local:compute'}, max_iterations=1)
        self.assertEqual(result['status'], 'limit_reached')
        self.assertEqual(result['iterations'][0]['receipts'][0]['error']['code'], 'provider_failure')
        self.assertEqual(self.reg.read()[-1]['kind'], 'run')

    def test_cancellation_between_iterations_keeps_prior_receipt(self):
        # First call permits execution; cancellation after the first failing iteration stops retries.
        class CancelAfterCall(WordLensAdapter):
            called = False
            def invoke(self, inputs, permissions):
                self.called = True
                return super().invoke(inputs, permissions)
        adapter = CancelAfterCall()
        result = Engine(self.reg, {'wordlens': adapter}).run(
            {'text': 7}, execute=True, permissions={'local:compute'}, max_iterations=5,
            cancel=lambda: adapter.called)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(len(result['iterations']), 1)

    def test_reorder_and_duplicate_lines_detected(self):
        lines = self.path.read_text().splitlines(keepends=True)
        for content in (''.join(reversed(lines)), ''.join(lines + [lines[0]])):
            self.path.write_text(content)
            with self.assertRaises(RegisterError):
                self.reg.read()

    def test_demo_cancellation_does_not_grant_consent(self):
        result = demonstrate(self.reg, execute=True, operator='tester', cancel=lambda: True)
        self.assertEqual(result['status'], 'cancelled')
        self.assertNotIn('demo.words', self.reg.approvals())
        self.assertFalse(any(e['kind'] == 'verification' for e in self.reg.read()))

    def test_wordlens_is_independently_runnable(self):
        result = subprocess.run([sys.executable, '-m', 'ear.providers.wordlens'],
                                input='one two three', capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), {'words': 3, 'characters': 13})


if __name__ == '__main__':
    unittest.main()
