"""Make a deterministic compressed O2R, preserving every runtime resource byte."""
import argparse
import json
import zipfile
from pathlib import Path

COURSE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=COURSE / 'build/silverstone-v1.9.o2r')
    args = parser.parse_args()
    source = args.input.resolve()
    target = COURSE / 'runtime/silverstone-v1.9.o2r'
    if source == target.resolve():
        parser.error('Use the built archive as input, not the bundled output.')
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(source) as original:
        assert original.testzip() is None
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as compressed:
            for name in sorted(original.namelist()):
                entry = zipfile.ZipInfo(name, (2026, 10, 4, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                compressed.writestr(entry, original.read(name), compresslevel=9)
        with zipfile.ZipFile(target) as compressed:
            assert compressed.testzip() is None
            assert set(original.namelist()) == set(compressed.namelist())
            assert all(original.read(name) == compressed.read(name) for name in original.namelist())
    info = {'id': 'silverstone', 'title': 'Silverstone',
            'archive': 'courses/silverstone/silverstone-v1.9.o2r'}
    web = COURSE.parents[1] / 'web/courses.json'
    web.write_text(json.dumps({'version': 1, 'courses': [info]}, indent=2) + '\n')
    print(json.dumps(info, indent=2))


if __name__ == '__main__':
    main()
