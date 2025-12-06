'''
Download and install plugin
'''

import argparse
import os.path
import sys
import subprocess
from onsdriver._ghutil import download_asset_with_file_re


def _is_cmake_build_dir(path):
    return os.path.isfile(path + '/CMakeCache.txt')

def _install_plugin_cmake_build(path):
    subprocess.run(['cmake', '--install', path], check=True)


if sys.platform == 'darwin':
    # pylint: disable=protected-access
    import onsdriver._plugin_install_macos

    def _download_plugin(repo_name, **kwargs):
        return download_asset_with_file_re(repo_name, r'.*macos.*\.zip', **kwargs)

    def _install_plugin(filename):
        if _is_cmake_build_dir(filename):
            return _install_plugin_cmake_build(filename)
        if filename.endswith('.zip'):
            return onsdriver._plugin_install_macos.install_plugin_macos_zip(filename)
        if filename.endswith('.pkg'):
            return onsdriver._plugin_install_macos.install_plugin_macos_pkg(filename)
        raise ValueError(f'Unknown type to install: {filename}')

elif sys.platform == 'win32':
    # pylint: disable=protected-access
    import onsdriver._plugin_install_win

    def _download_plugin(repo_name, **kwargs):
        return download_asset_with_file_re(repo_name, r'.*[Ww]indows.*\.zip', **kwargs)

    def _install_plugin(filename):
        if filename.endswith('.zip'):
            return onsdriver._plugin_install_win.install_plugin_windows_zip(filename)
        raise ValueError(f'Unknown type to install: {filename}')

elif sys.platform == 'linux':
    # On Linux, user need to install into the system, hence let's ignore to install.
    # pylint: disable=unused-argument
    def _download_plugin(repo_name, **kwargs):
        return ''
    def _install_plugin(filename):
        return None

else:
    def _download_plugin(repo_name, **kwargs):
        raise NotImplementedError(f'_download_plugin on {sys.platform}')
    def _install_plugin(filename):
        raise NotImplementedError(f'_install_plugin on {sys.platform}')

def download_plugin(repo_name, info_only=False):
    '''Download plugin from github.com
    :param repo_name:  Repository URL like "https://github.com/owner/repo"
    :param info_only:  Return asset information in JSON string without downloading the file.
    :return:           Path to the downloaded file.
    '''
    return _download_plugin(repo_name, info_only=info_only)

def install_plugin(filename):
    '''Install plugin
    :param filename:  Path to the plugin file, ZIP or PKG.
    '''
    return _install_plugin(filename)

def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info-only', action='store_true', default=None,
                        help='Print the asset information and exit')
    parser.add_argument('names', nargs='+', default=[],
                        help='Repository URL like "https://github.com/owner/repo"')
    args = parser.parse_args()
    return args

def main():
    'Entry point'
    args = _get_args()

    paths = []
    for name in args.names:
        if os.path.isfile(name):
            paths.append(name)
        elif _is_cmake_build_dir(name):
            paths.append(name)
        elif name.startswith('http://') or name.startswith('https://'):
            path = download_plugin(name, info_only=args.info_only)
            paths.append(path)
        else:
            sys.stderr.write(f'Error: {name}: Unknown type.\n')
            sys.exit(1)

    if args.info_only:
        for path in paths:
            print(path)
        return

    for path in paths:
        install_plugin(path)

if __name__ == '__main__':
    main()
