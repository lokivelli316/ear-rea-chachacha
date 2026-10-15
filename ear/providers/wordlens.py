"""Original whitespace word counter, independently usable without EAR's engine."""
import json
import sys


def count(text):
    return {'words': len(text.split()), 'characters': len(text)}


def main():
    print(json.dumps(count(sys.stdin.read()), sort_keys=True))


if __name__ == '__main__':
    main()
