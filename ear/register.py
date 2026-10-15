"""Append-only, hash-chained JSONL register with strict replay and POSIX locking."""

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import re


class RegisterError(ValueError):
    """Invalid event, duplicate identity, or damaged register."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class Register:
    KINDS = {'feature', 'evidence', 'decision', 'verification', 'iteration', 'run'}

    def __init__(self, path):
        self.path = Path(path)

    @contextmanager
    def _locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a+', encoding='utf-8') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            try:
                yield stream
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    @staticmethod
    def _validate(kind, feature_id, data, features):
        if kind not in Register.KINDS or not isinstance(data, dict):
            raise RegisterError('Unknown event kind or invalid data')
        if kind == 'feature':
            if not isinstance(feature_id, str) or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{0,79}', feature_id):
                raise RegisterError('Feature ID must be a stable lowercase identifier')
            if feature_id in features:
                raise RegisterError('Duplicate feature ID: ' + feature_id)
            required = ('intent', 'source', 'strategy', 'adapter', 'evidence', 'test_plan')
            if any(not data.get(key) for key in required):
                raise RegisterError('Feature metadata is incomplete')
            if data['strategy'] not in {'rebuild', 'reuse', 'connect'}:
                raise RegisterError('Unknown strategy')
            if not isinstance(data['source'], dict) or any(not isinstance(data['source'].get(k), str) or not data['source'][k].strip() for k in ('name', 'version', 'license')):
                raise RegisterError('Source name, version and license notes are required')
            if any(not isinstance(data[k], str) for k in ('intent', 'adapter', 'evidence', 'test_plan')):
                raise RegisterError('Feature text fields must be strings')
        elif kind in {'evidence', 'decision', 'verification'}:
            if feature_id not in features:
                raise RegisterError('Unknown feature ID')
        elif feature_id is not None:
            raise RegisterError('Run and iteration events are not feature-scoped')
        if kind == 'decision' and (type(data.get('approved')) is not bool or not isinstance(data.get('operator'), str) or not data['operator'].strip()):
            raise RegisterError('Decision requires explicit boolean consent and an operator')

    def _read(self, stream):
        stream.seek(0)
        events, features = [], set()
        previous = None
        for number, line in enumerate(stream, 1):
            try:
                if not line.endswith('\n'):
                    raise ValueError('incomplete line')
                event = json.loads(line)
                if set(event) != {'sequence', 'timestamp', 'kind', 'feature_id', 'data', 'previous', 'checksum'}:
                    raise ValueError('invalid fields')
                checksum = event['checksum']
                unsigned = {k: v for k, v in event.items() if k != 'checksum'}
                if event['sequence'] != number or event['previous'] != previous or digest(unsigned) != checksum:
                    raise ValueError('sequence or checksum mismatch')
                timestamp = event['timestamp']
                if not isinstance(timestamp, str) or not timestamp.endswith('Z'):
                    raise ValueError('invalid timestamp')
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                self._validate(event['kind'], event['feature_id'], event['data'], features)
                if event['kind'] == 'feature':
                    features.add(event['feature_id'])
                events.append(event)
                previous = checksum
            except (ValueError, KeyError, TypeError, OverflowError) as exc:
                raise RegisterError(f'Corrupt register at line {number}: {exc}') from exc
        return events

    def read(self):
        if not self.path.exists():
            return []
        with self._locked() as stream:
            return self._read(stream)

    def record(self, kind, feature_id, data):
        import os
        with self._locked() as stream:
            events = self._read(stream)
            features = {e['feature_id'] for e in events if e['kind'] == 'feature'}
            self._validate(kind, feature_id, data, features)
            event = {'sequence': len(events) + 1,
                     'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                     'kind': kind, 'feature_id': feature_id, 'data': data,
                     'previous': events[-1]['checksum'] if events else None}
            event['checksum'] = digest(event)
            stream.seek(0, 2)
            stream.write(canonical(event) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
            return event

    def add_feature(self, feature_id, **metadata):
        return self.record('feature', feature_id, metadata)

    def decide(self, feature_id, *, approved, operator):
        return self.record('decision', feature_id, {'approved': approved, 'operator': operator})

    def features(self):
        return {e['feature_id']: e['data'] for e in self.read() if e['kind'] == 'feature'}

    def approvals(self):
        return {e['feature_id']: e['data']['approved'] for e in self.read() if e['kind'] == 'decision'}
