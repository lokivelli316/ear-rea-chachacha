import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ear.register import Register, RegisterError
from ear.adapters import WordLensAdapter, JsonToolAdapter
from ear.engine import Engine
from ear.demo import demonstrate


class SliceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'register.jsonl'
        self.reg = Register(self.path)

    def feature(self, ident='words', adapter='wordlens'):
        return self.reg.add_feature(ident, intent='Count words locally',
            source={'name': 'GNU wc', 'version': 'documented semantics',
                    'license': 'GPL; no source copied'},
            strategy='rebuild', adapter=adapter,
            evidence='Whitespace-separated word count; original implementation',
            test_plan='Run deterministic word fixtures')

    def test_register_append_replay_duplicate_and_hash(self):
        self.feature()
        before = self.path.read_bytes()
        self.reg.record('evidence', 'words', {'note': 'observed three tokens'})
        self.assertTrue(self.path.read_bytes().startswith(before))
        self.assertEqual(Register(self.path).features()['words']['intent'], 'Count words locally')
        self.assertEqual(len(self.reg.read()), 2)
        self.assertEqual(len(self.reg.read()[0]['checksum']), 64)
        with self.assertRaises(RegisterError):
            self.feature()
        self.assertEqual(len(self.reg.read()), 2)

    def test_corrupted_register_blocks_read_and_append(self):
        self.feature()
        content = self.path.read_text().replace('Count words locally', 'tampered')
        self.path.write_text(content)
        with self.assertRaises(RegisterError):
            self.reg.read()
        with self.assertRaises(RegisterError):
            self.reg.record('evidence', 'words', {'note': 'x'})
        self.assertEqual(self.path.read_text(), content)

    def test_truncated_register_and_invalid_event_rejected(self):
        self.path.write_text('{"partial":')
        with self.assertRaises(RegisterError):
            self.reg.read()
        self.path.unlink()
        with self.assertRaises(RegisterError):
            self.reg.record('evidence', 'missing', {})
        with self.assertRaises(RegisterError):
            self.reg.record('arbitrary', None, {})

    def test_adapters_alone_schema_permissions_disconnect(self):
        word = WordLensAdapter()
        self.assertEqual(word.invoke({'text': 'one\ttwo\nthree'}, {'local:compute'})['output']['words'], 3)
        self.assertEqual(word.invoke({'text': ''}, {'local:compute'})['output']['words'], 0)
        self.assertEqual(word.invoke({'text': 1}, {'local:compute'})['error']['code'], 'invalid_input')
        self.assertEqual(word.invoke({'text': 'x'}, set())['error']['code'], 'permission_refused')
        js = JsonToolAdapter()
        receipt = js.invoke({'document': {'b': 2, 'a': 1}}, {'local:subprocess'})
        self.assertEqual(json.loads(receipt['output']['formatted']), {'a': 1, 'b': 2})
        self.assertIn('json.tool', receipt['provenance']['source'])
        js.disconnect()
        self.assertFalse(js.health()['available'])
        self.assertEqual(js.invoke({'document': {}}, {'local:subprocess'})['error']['code'], 'disconnected')
        self.assertEqual(word.invoke({'text': 'still works'}, {'local:compute'})['output']['words'], 2)

    def test_dry_run_needs_no_consent_and_never_invokes(self):
        self.feature()
        adapter = WordLensAdapter()
        adapter.disconnect()
        result = Engine(self.reg, {'wordlens': adapter}).run({'text': 'one'}, max_iterations=2)
        self.assertEqual(result['status'], 'dry_run')
        self.assertEqual(result['iterations'], [])
        self.assertEqual(result['queue'], ['words'])
        self.assertFalse(any(e['kind'] == 'verification' for e in self.reg.read()))

    def test_consent_refusal_and_bounded_failure(self):
        self.feature()
        engine = Engine(self.reg, {'wordlens': WordLensAdapter()})
        result = engine.run({'text': 'a'}, execute=True, max_iterations=3)
        self.assertEqual(result['status'], 'permission_refused')
        self.assertEqual(result['iterations'], [])
        self.reg.decide('words', approved=True, operator='test operator')
        result = engine.run({'text': 1}, execute=True, permissions={'local:compute'}, max_iterations=2)
        self.assertEqual(result['status'], 'limit_reached')
        self.assertEqual(len(result['iterations']), 2)
        self.assertEqual(len([e for e in self.reg.read() if e['kind'] == 'verification']), 2)
        self.assertEqual(result['iterations'][0]['receipts'][0]['error']['code'], 'invalid_input')

    def test_acceptance_cancellation_and_revocation(self):
        self.feature()
        self.reg.decide('words', approved=True, operator='tester')
        engine = Engine(self.reg, {'wordlens': WordLensAdapter()})
        result = engine.run({'text': 'one two'}, execute=True, permissions={'local:compute'}, max_iterations=5)
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(len(result['iterations']), 1)
        self.assertEqual(result['iterations'][0]['receipts'][0]['output']['words'], 2)
        result = engine.run({}, execute=True, cancel=lambda: True)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(result['iterations'], [])
        self.reg.decide('words', approved=False, operator='tester')
        self.assertEqual(engine.run({}, execute=True)['status'], 'permission_refused')
        for invalid in (0, -1, 101, True):
            with self.assertRaises(ValueError):
                engine.run({}, max_iterations=invalid)

    def test_demo_two_providers_degrades_and_replay_is_safe(self):
        result = demonstrate(self.reg, execute=True, operator='tester')
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['alone']['wordlens']['output']['words'], 3)
        self.assertTrue(result['alone']['json-tool']['ok'])
        self.assertEqual(result['together']['status'], 'accepted')
        self.assertEqual(result['disconnected']['status'], 'degraded')
        self.assertTrue(result['disconnected']['iterations'][0]['receipts'][0]['ok'])
        self.assertEqual(result['disconnected']['iterations'][0]['receipts'][1]['error']['code'], 'disconnected')
        demonstrate(self.reg, execute=True, operator='tester')
        self.assertEqual(len(self.reg.features()), 2)
        self.assertTrue(all(e['timestamp'].endswith('Z') for e in self.reg.read()))

    def test_cli_dry_run_execute_and_corruption_exit(self):
        def cli(*args):
            return subprocess.run([sys.executable, '-m', 'ear', '--register', str(self.path), *args], capture_output=True, text=True)
        dry = cli('demo')
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(json.loads(dry.stdout)['status'], 'dry_run')
        refused = cli('demo', '--execute')
        self.assertNotEqual(refused.returncode, 0)
        executed = cli('demo', '--execute', '--approve', '--operator', 'test')
        self.assertEqual(executed.returncode, 0, executed.stderr)
        self.assertEqual(json.loads(executed.stdout)['status'], 'verified')
        replay = cli('replay')
        self.assertEqual(replay.returncode, 0, replay.stderr)
        self.assertGreater(len(json.loads(replay.stdout)['events']), 0)
        self.path.write_text('broken\n')
        corrupt = cli('replay')
        self.assertEqual(corrupt.returncode, 2)
        self.assertEqual(json.loads(corrupt.stdout)['status'], 'error')


if __name__ == '__main__':
    unittest.main()
