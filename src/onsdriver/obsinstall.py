'''
Download and extract OBS Studio from GitHub
'''

import argparse
import shutil
import sys
import subprocess
import zipfile
from onsdriver import util
from onsdriver._ghutil import download_asset_with_file_re


_OBS_REPO = 'https://github.com/obsproject/obs-studio'

def _extract(pkg_path, destination):
    if pkg_path.endswith('.zip'):
        with zipfile.ZipFile(pkg_path) as z:
            z.extractall(destination)
    elif pkg_path.endswith('.dmg') and sys.platform == 'darwin':
        import dmglib # pylint: disable=import-outside-toplevel,import-error
        with dmglib.attachedDiskImage(pkg_path) as mount_points:
            shutil.copytree(mount_points[0], destination, symlinks=True)
    else:
        subprocess.run(['7z', 'x', '-o'+destination, pkg_path], check=True)
    util.ignore_directory(destination)

def install_obs(destination='./obs-studio', selector_re=None, info_only=False):
    '''Download OBS Studio from GitHub release and install it.
    :param destination:  Destination to extract OBS Studio.
    :param selector_re:  Regular expression to select the file.
    '''

    if not selector_re:
        if sys.platform == 'darwin':
            selector_re = r'^OBS-Studio-.*-macOS-Apple.dmg$'
        elif sys.platform == 'win32':
            selector_re = r'^OBS-Studio-.*-Windows-x64.zip$'
        else:
            raise NotImplementedError(f'Not supported platform: {sys.platform}')

    pkg_path = download_asset_with_file_re(_OBS_REPO, selector_re, info_only=info_only)
    if info_only:
        return pkg_path

    _extract(pkg_path=pkg_path, destination=destination)
    return None


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--destination', action='store', default='./obs-studio')
    parser.add_argument('--info-only', action='store_true', default=None,
                        help='Print the asset information and exit')
    args = parser.parse_args()
    return args

def main():
    'Entry point'
    args = _get_args()

    ret = install_obs(destination=args.destination, info_only=args.info_only)

    if args.info_only:
        print(ret)

if __name__ == '__main__':
    main()
