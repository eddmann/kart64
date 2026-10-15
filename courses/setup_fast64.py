"""Fetch the exact HarbourMasters Fast64 source used by the course generator."""
import argparse
import subprocess
from pathlib import Path

COMMIT = '0f7a80a6b40c73a8d65dd2dab37310c163f54c68'
REPOSITORY = 'https://github.com/HarbourMasters/fast64.git'
DEFAULT_PATH = Path(__file__).resolve().parents[1] / '.cache/course-tools/fast64'


def verify(path):
    """Refuse a different or modified tool version instead of overwriting it."""
    if path.name != 'fast64':
        raise ValueError('The addon directory must be named fast64 (its Python package name).')
    revision = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    changes = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain', '--untracked-files=no'], text=True)
    if revision != COMMIT or changes:
        raise ValueError(f'Fast64 must be an unmodified checkout of {COMMIT}: {path}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--path', type=Path, default=DEFAULT_PATH)
    args = parser.parse_args()
    path = args.path.resolve()
    if path.name != 'fast64':
        parser.error('The addon directory must be named fast64.')
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--no-checkout', '--filter=blob:none', REPOSITORY, str(path)], check=True)
        subprocess.run(['git', '-C', str(path), 'checkout', '--detach', COMMIT], check=True)
    verify(path)
    print(f'Fast64 {COMMIT}: {path}', flush=True)


if __name__ == '__main__':
    main()
