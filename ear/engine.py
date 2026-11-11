"""Deterministic queue order, explicit consent, and a bounded ChaChaCha loop."""

from uuid import uuid4


class Engine:
    def __init__(self, register, adapters):
        self.register = register
        self.adapters = adapters

    def run(self, inputs, *, execute=False, permissions=None, max_iterations=3,
            cancel=None, feature_ids=None):
        if type(max_iterations) is not int or not 1 <= max_iterations <= 100:
            raise ValueError('max_iterations must be an integer from 1 to 100')
        features = self.register.features()
        queue = list(features) if feature_ids is None else list(feature_ids)
        if len(queue) != len(set(queue)) or any(f not in features for f in queue):
            raise ValueError('Queue must contain unique registered feature IDs')
        result = {'run_id': str(uuid4()), 'status': 'dry_run', 'queue': queue,
                  'max_iterations': max_iterations, 'iterations': [],
                  'limitations': ['Local fixture verification only; no REA integration or deployment']}
        if not execute:
            result['plan'] = [{'feature_id': f, 'adapter': features[f]['adapter'],
                               'strategy': features[f]['strategy']} for f in queue]
            return self._finish(result)
        if cancel and cancel():
            result['status'] = 'cancelled'
            return self._finish(result)
        if not queue:
            result['status'] = 'empty_queue'
            return self._finish(result)
        for number in range(1, max_iterations + 1):
            if cancel and cancel():
                result['status'] = 'cancelled'
                break
            # Read decisions again so revocations are respected between iterations.
            approved = self.register.approvals()
            if any(not approved.get(f, False) for f in queue):
                result['status'] = 'permission_refused'
                break
            receipts = []
            for feature_id in queue:
                if cancel and cancel():
                    result['status'] = 'cancelled'
                    break
                adapter = self.adapters.get(features[feature_id]['adapter'])
                if adapter is None:
                    receipt = {'ok': False, 'adapter': features[feature_id]['adapter'],
                               'error': {'code': 'unavailable', 'message': 'Adapter is not registered'}, 'output': None}
                else:
                    try:
                        receipt = adapter.invoke(inputs, set(permissions or ()))
                    except Exception as exc:
                        # A provider failure must not discard earlier verification receipts.
                        receipt = {'ok': False, 'adapter': features[feature_id]['adapter'],
                                   'provenance': adapter.descriptor.get('provenance', {}),
                                   'error': {'code': 'provider_failure', 'message': str(exc)},
                                   'output': None}
                receipt = dict(receipt, feature_id=feature_id)
                receipts.append(receipt)
                self.register.record('verification', feature_id,
                    {'run_id': result['run_id'], 'iteration': number, 'receipt': receipt})
            iteration = {'run_id': result['run_id'], 'number': number, 'receipts': receipts}
            self.register.record('iteration', None, iteration)
            result['iterations'].append(iteration)
            if result['status'] == 'cancelled':
                break
            if all(r['ok'] for r in receipts):
                result['status'] = 'accepted'
                break
            if any(r['ok'] for r in receipts):
                result['status'] = 'degraded'
                break
            result['status'] = 'limit_reached'
        return self._finish(result)

    def _finish(self, result):
        self.register.record('run', None, result)
        return result
