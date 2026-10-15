"""Mosaic Desk: a third application composing WordLens and CPython json.tool."""

import json
import sys

from .adapters import WordLensAdapter, JsonToolAdapter
from .engine import Engine

FIXTURE = {'text': 'federate do not-fuse', 'document': {'project': 'Mosaic Desk', 'features': 2}}
PERMISSIONS = {'local:compute', 'local:subprocess'}


def demonstrate(register, *, execute=False, operator=None):
    features = register.features()
    definitions = [
        ('demo.words', 'wordlens', 'rebuild',
         {'name': 'GNU wc capability / original WordLens sample', 'version': 'WordLens 1',
          'license': 'GNU wc is GPL; behavior studied, no source copied'},
         'GNU wc documentation: words separated by whitespace; WordLens uses str.split(). '
         'Subset only: no byte, locale, or file-count compatibility claim.'),
        ('demo.json', 'json-tool', 'connect',
         {'name': 'CPython json.tool', 'version': sys.version.split()[0],
          'license': 'Python Software Foundation License'},
         'Documented python -m json.tool stdin/stdout interface, exercised locally.')]
    for ident, adapter, strategy, source, evidence in definitions:
        if ident not in features:
            register.add_feature(ident, intent='Compose local capabilities in Mosaic Desk',
                source=source, strategy=strategy, adapter=adapter, evidence=evidence,
                test_plan='Verify each provider, composition, then disconnect json.tool',
                limitations='Small deterministic fixture, not full provider compatibility')
        elif features[ident]['adapter'] != adapter or features[ident]['strategy'] != strategy:
            raise ValueError('Demo feature ID conflicts with existing registration: ' + ident)
    adapters = {'wordlens': WordLensAdapter(), 'json-tool': JsonToolAdapter()}
    engine = Engine(register, adapters)
    queue = ['demo.words', 'demo.json']
    if not execute:
        return engine.run(FIXTURE, feature_ids=queue)
    if not operator or not operator.strip():
        return {'status': 'permission_refused', 'reason': 'Explicit approval and operator identity required'}
    for ident in queue:
        register.decide(ident, approved=True, operator=operator)
    alone = {}
    for ident, adapter in zip(queue, adapters.values()):
        receipt = adapter.invoke(FIXTURE, PERMISSIONS)
        register.record('verification', ident, {'scenario': 'alone', 'receipt': receipt})
        alone[adapter.descriptor['id']] = receipt
    together = engine.run(FIXTURE, execute=True, permissions=PERMISSIONS, feature_ids=queue)
    adapters['json-tool'].disconnect()
    disconnected = engine.run(FIXTURE, execute=True, permissions=PERMISSIONS, feature_ids=queue)
    checks = {
        'word_count': alone['wordlens']['ok'] and alone['wordlens']['output']['words'] == 3,
        'json_roundtrip': alone['json-tool']['ok'] and json.loads(alone['json-tool']['output']['formatted']) == FIXTURE['document'],
        'composition': together['status'] == 'accepted',
        'disconnect': disconnected['status'] == 'degraded',
    }
    result = {'application': 'Mosaic Desk', 'status': 'verified' if all(checks.values()) else 'failed',
              'checks': checks, 'alone': alone, 'together': together, 'disconnected': disconnected,
              'rea': 'UNKNOWN: optional external integration, not invoked'}
    register.record('run', None, result)
    return result
