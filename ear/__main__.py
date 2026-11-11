"""Machine-readable CLI. Execution always requires explicit approval/permissions."""

import argparse
import json
from pathlib import Path
import signal
import sys

from .adapters import WordLensAdapter, JsonToolAdapter
from .demo import demonstrate
from .engine import Engine
from .register import Register, RegisterError


def parser():
    root = argparse.ArgumentParser(prog='ear', description=__doc__)
    root.add_argument('--register', default='.ear/register.jsonl')
    sub = root.add_subparsers(dest='command', required=True)
    demo = sub.add_parser('demo', help='Run the deterministic Mosaic Desk demonstration')
    demo.add_argument('--execute', action='store_true')
    demo.add_argument('--approve', action='store_true', help='Consent to the two bundled local demo capabilities')
    demo.add_argument('--operator')
    sub.add_parser('replay', help='Validate and read the register without executing providers')
    sub.add_parser('capabilities', help='Describe bundled adapters and their health')
    add = sub.add_parser('add', help='Append a feature from a JSON metadata file')
    add.add_argument('feature_id')
    add.add_argument('--metadata', required=True, type=Path)
    decision = sub.add_parser('decide', help='Append an operator consent decision')
    decision.add_argument('feature_id')
    decision.add_argument('--operator', required=True)
    choice = decision.add_mutually_exclusive_group(required=True)
    choice.add_argument('--approve', action='store_true')
    choice.add_argument('--refuse', action='store_true')
    run = sub.add_parser('run', help='Plan or run the registered queue')
    run.add_argument('--input', required=True, type=Path, help='JSON input object')
    run.add_argument('--execute', action='store_true')
    run.add_argument('--permission', action='append', default=[], choices=['local:compute', 'local:subprocess'])
    run.add_argument('--max-iterations', type=int, default=3)
    run.add_argument('--feature', action='append', help='Select registered feature IDs; default all')
    return root


def main(argv=None):
    args = parser().parse_args(argv)
    register = Register(args.register)
    cancelled = False

    def stop(signum, frame):
        nonlocal cancelled
        cancelled = True

    previous = signal.signal(signal.SIGINT, stop)
    try:
        if args.command == 'demo':
            result = demonstrate(register, execute=args.execute,
                                 operator=args.operator if args.approve else None, cancel=lambda: cancelled)
        elif args.command == 'replay':
            result = {'status': 'replayed', 'events': register.read(), 'features': register.features()}
        elif args.command == 'capabilities':
            result = {'status': 'described', 'capabilities': [
                {'descriptor': a.descriptor, 'health': a.health()}
                for a in (WordLensAdapter(), JsonToolAdapter())]}
        elif args.command == 'add':
            metadata = json.loads(args.metadata.read_text())
            if not isinstance(metadata, dict):
                raise ValueError('metadata must be a JSON object')
            result = {'status': 'registered', 'event': register.add_feature(args.feature_id, **metadata)}
        elif args.command == 'decide':
            result = {'status': 'recorded', 'event': register.decide(args.feature_id,
                       approved=args.approve, operator=args.operator)}
        else:
            inputs = json.loads(args.input.read_text())
            if not isinstance(inputs, dict):
                raise ValueError('input must be a JSON object')
            result = Engine(register, {'wordlens': WordLensAdapter(), 'json-tool': JsonToolAdapter()}).run(
                inputs, execute=args.execute, permissions=args.permission,
                max_iterations=args.max_iterations, cancel=lambda: cancelled, feature_ids=args.feature)
        print(json.dumps(result, sort_keys=True, allow_nan=False))
        return 0 if result['status'] in {'verified', 'dry_run', 'accepted', 'replayed', 'described', 'registered', 'recorded'} else 1
    except (RegisterError, ValueError, TypeError, OSError) as exc:
        print(json.dumps({'status': 'error', 'error': str(exc)}, sort_keys=True))
        return 2
    finally:
        signal.signal(signal.SIGINT, previous)


if __name__ == '__main__':
    sys.exit(main())
