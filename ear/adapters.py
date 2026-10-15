"""Fixed local capabilities; no plugin loading, shell interpolation, or downloads."""

from dataclasses import dataclass, field
import json
import subprocess
import sys
from typing import Protocol

from .providers.wordlens import count
from .register import digest


class CapabilityAdapter(Protocol):
    descriptor: dict

    def health(self) -> dict: ...
    def disconnect(self) -> None: ...
    def invoke(self, inputs: dict, permissions: set[str]) -> dict: ...


@dataclass
class LocalAdapter:
    descriptor: dict
    connected: bool = field(default=True, init=False)

    def health(self):
        return {'available': self.connected, 'adapter': self.descriptor['id']}

    def disconnect(self):
        self.connected = False

    def invoke(self, inputs, permissions):
        receipt = {'adapter': self.descriptor['id'], 'ok': False,
                   'provenance': self.descriptor['provenance'],
                   'artifact_owner': 'operator', 'output': None, 'error': None}
        try:
            receipt['input_checksum'] = digest(inputs)
            if not self.connected:
                return self._error(receipt, 'disconnected', 'Provider was disconnected')
            if not set(self.descriptor['permissions']).issubset(permissions):
                return self._error(receipt, 'permission_refused', 'Required local permission was not granted')
            key = self.descriptor['input_key']
            if not isinstance(inputs, dict) or key not in inputs:
                return self._error(receipt, 'invalid_input', 'Missing input: ' + key)
            value = inputs[key]
            if key == 'text' and not isinstance(value, str):
                return self._error(receipt, 'invalid_input', 'text must be a string')
            output = self._perform(value)
            receipt.update(ok=True, output=output, output_checksum=digest(output))
            return receipt
        except (ValueError, TypeError, RecursionError) as exc:
            return self._error(receipt, 'invalid_input', str(exc))
        except (OSError, subprocess.SubprocessError) as exc:
            return self._error(receipt, 'provider_failure', str(exc))

    @staticmethod
    def _error(receipt, code, message):
        receipt['error'] = {'code': code, 'message': message}
        return receipt

    def _perform(self, value):
        raise NotImplementedError


class WordLensAdapter(LocalAdapter):
    def __init__(self):
        super().__init__({
            'id': 'wordlens', 'version': '1', 'operations': ['count'], 'input_key': 'text',
            'input_schema': {'type': 'object', 'required': ['text'], 'properties': {'text': {'type': 'string'}}},
            'output_schema': {'type': 'object', 'required': ['words', 'characters'], 'properties': {'words': {'type': 'integer'}, 'characters': {'type': 'integer'}}},
            'permissions': ['local:compute'], 'compatibility': 'Python 3.11+',
            'provenance': {'source': 'EAR WordLens sample; inspired by GNU wc word semantics',
                           'strategy': 'rebuild', 'license': 'Original implementation; no GNU source copied'},
            'cancellation': 'Between calls; synchronous bounded local computation',
            'artifact_owner': 'operator'})

    def _perform(self, value):
        return count(value)


class JsonToolAdapter(LocalAdapter):
    def __init__(self):
        super().__init__({
            'id': 'json-tool', 'version': '1', 'operations': ['format'], 'input_key': 'document',
            'input_schema': {'type': 'object', 'required': ['document'], 'properties': {'document': {'description': 'Finite JSON value'}}},
            'output_schema': {'type': 'object', 'required': ['formatted'], 'properties': {'formatted': {'type': 'string'}}},
            'permissions': ['local:subprocess'], 'compatibility': 'Python 3.11+ stdlib json.tool',
            'provenance': {'source': 'CPython json.tool', 'version': sys.version.split()[0],
                           'strategy': 'connect', 'license': 'Python Software Foundation License'},
            'cancellation': 'Between calls; subprocess timeout 5 seconds',
            'artifact_owner': 'operator'})

    def health(self):
        health = super().health()
        health['runtime'] = sys.version.split()[0]
        return health

    def _perform(self, value):
        serialized = json.dumps(value, allow_nan=False)
        result = subprocess.run([sys.executable, '-I', '-m', 'json.tool', '--sort-keys'],
                                input=serialized, capture_output=True, text=True, timeout=5,
                                check=True)
        return {'formatted': result.stdout}
