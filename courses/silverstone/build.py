"""Generate and validate the native Silverstone course from text sources."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

COURSE = Path(__file__).resolve().parent
SOURCE = COURSE / 'project'
PROJECT = COURSE / 'build/work/project'
sys.path.insert(0, str(COURSE.parent))
from setup_fast64 import COMMIT, DEFAULT_PATH, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blender', default='blender', help='Blender 4.3.2 executable')
    parser.add_argument('--fast64', type=Path, default=DEFAULT_PATH)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--regenerate-textures', action='store_true', help='Generate the original artwork instead of using the checked-in texture PNGs')
    parser.add_argument('--from-blend', action='store_true', help='Export the edited project/silverstone.blend instead of generating meshes from scripts')
    args = parser.parse_args()
    if args.threads < 1:
        parser.error('--threads must be positive')
    fast64 = args.fast64.resolve()
    verify(fast64)
    version = subprocess.check_output([args.blender, '--version'], text=True).splitlines()[0]
    if version != 'Blender 4.3.2':
        parser.error(f'Expected Blender 4.3.2, found {version}')
    # Build in an ignored workspace; keep all checked-in editing files intact.
    if PROJECT.exists():
        shutil.rmtree(PROJECT)
    for directory in ['scripts', 'source', 'textures']:
        shutil.copytree(SOURCE / directory, PROJECT / directory,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    def run(command):
        print('Running:', ' '.join(map(str, command)), flush=True)
        subprocess.run(list(map(str, command)), cwd=PROJECT, check=True)

    def python(script):
        run([sys.executable, 'scripts/' + script])

    def blender(script, blend=None, addon=False):
        command = [args.blender, '--factory-startup', '-b']
        if blend:
            command.append(str(PROJECT / blend))
        command += ['-t', str(args.threads), '--python-exit-code', '1', '--python', str(PROJECT / 'scripts' / script)]
        if addon:
            command += ['--', '--fast64', str(fast64)]
        run(command)

    if not args.from_blend:
        python('prepare_pit_lane.py')
    if args.regenerate_textures:
        python('make_textures.py')
        python('make_spectator_texture.py')
    if args.from_blend:
        shutil.copyfile(SOURCE / 'silverstone.blend', PROJECT / 'silverstone.blend')
        blender('export_existing.py', 'silverstone.blend', addon=True)
    else:
        blender('build_course.py', addon=True)
    python('package_course.py')
    if args.regenerate_textures:
        python('make_hd_textures.py')
    python('package_hd_course.py')
    python('validate_course.py')
    blender('validate_blend.py', 'silverstone.blend')
    blender('check_clearance.py', 'silverstone.blend')
    output = COURSE / 'build'
    output.mkdir(exist_ok=True)
    archive = output / 'silverstone-v1.9.o2r'
    shutil.copyfile(PROJECT / 'silverstone-hd-complete.o2r', archive)
    info = {'version': '1.9.0', 'blender': version, 'fast64_commit': COMMIT,
            'mesh_source': 'edited Blender project' if args.from_blend else 'procedural generators',
            'textures_regenerated': args.regenerate_textures,
            'course_file': archive.name, 'bytes': archive.stat().st_size,
            'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
            'static_validation': 'passed', 'native_playtest_of_this_build': False}
    (output / 'build-info.json').write_text(json.dumps(info, indent=2) + '\n')
    print(f'Course ready: {archive}', flush=True)


if __name__ == '__main__':
    main()
