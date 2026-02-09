'''
Download and install plugin
'''

import argparse
import os.path
import re
import sys
import subprocess
import onsdriver.platform
from onsdriver._ghutil import download_asset_with_file_re


def _is_cmake_build_dir(path):
    return os.path.isfile(path + '/CMakeCache.txt')

def _install_plugin_cmake_build(path):
    subprocess.run(['cmake', '--install', path], check=True)


if onsdriver.platform.os_is_macos():
    # pylint: disable=protected-access
    import onsdriver._plugin_install_macos

    def _download_plugin(repo_name, **kwargs):
        file_re = r'.*macos.*\.zip'
        if 'text-pthread' in repo_name:
            a = onsdriver.platform.arch()
            if a == onsdriver.platform.ARCH_ARM64:
                file_re = r'.*macos.*(arm64|universal)\.zip'
            elif a == onsdriver.platform.ARCH_X86_64:
                file_re = r'.*macos.*(x86_64|universal)\.zip'
            else:
                raise NotImplementedError(f'Unknown architecture: {a}')

        return download_asset_with_file_re(repo_name, file_re, **kwargs)

    def _install_plugin(filename):
        if _is_cmake_build_dir(filename):
            return _install_plugin_cmake_build(filename)
        if filename.endswith('.zip'):
            return onsdriver._plugin_install_macos.install_plugin_macos_zip(filename)
        if filename.endswith('.pkg'):
            return onsdriver._plugin_install_macos.install_plugin_macos_pkg(filename)
        raise ValueError(f'Unknown type to install: {filename}')

elif onsdriver.platform.os_is_windows():
    # pylint: disable=protected-access
    import onsdriver._plugin_install_win

    def _download_plugin(repo_name, **kwargs):
        return download_asset_with_file_re(repo_name, r'.*[Ww]indows.*\.zip', **kwargs)

    def _install_plugin(filename):
        if filename.endswith('.exe'):
            return onsdriver._plugin_install_win.install_plugin_windows_exe(filename)
        if filename.endswith('.zip'):
            return onsdriver._plugin_install_win.install_plugin_windows_zip(filename)
        raise ValueError(f'Unknown type to install: {filename}')

elif onsdriver.platform.os_is_linux():
    # On Linux, user need to install into the system, hence let's ignore to install.
    # pylint: disable=unused-argument
    def _download_plugin(repo_name, **kwargs):
        return ''
    def _install_plugin(filename):
        return None

else:
    def _download_plugin(repo_name, **kwargs):
        raise NotImplementedError(f'_download_plugin on {onsdriver.platform.os_name()}')
    def _install_plugin(filename):
        raise NotImplementedError(f'_install_plugin on {onsdriver.platform.os_name()}')

def _version(s):
    def _safe_int(s):
        try:
            return int(s)
        except ValueError:
            return 0
    return tuple(map(_safe_int, s.split('.')))

class _FilterPlugins:
    # pylint: disable=too-few-public-methods
    def __init__(self, obs=None):
        self.obs = obs

    def filter(self, assets):
        'Filter the list of assets'
        re_obs = re.compile('[_-]obs([1-9][0-9.]*)[^0-9]')
        best_obs_v = None
        best_obs_ver = None
        limit_obs_v = _version(self.obs) if self.obs else None
        for a in assets:
            name = a['name']
            m = re_obs.search(name)
            if m:
                obs_ver = m[1]
                a['obs_ver'] = obs_ver
                obs_v = _version(obs_ver)
                if not limit_obs_v or obs_v <= limit_obs_v:
                    if not best_obs_v or obs_v > best_obs_v:
                        best_obs_v = obs_v
                        best_obs_ver = obs_ver

        if not best_obs_v:
            return assets

        return [a for a in assets if 'obs_ver' not in a or a['obs_ver'] == best_obs_ver]

def download_plugin(repo_name, info_only=False, obs=None):
    '''Download plugin from github.com
    :param repo_name:  Repository URL like "https://github.com/owner/repo"
    :param info_only:  Return asset information in JSON string without downloading the file.
    :param obs:        The version of OBS Studio.
    :return:           Path to the downloaded file.
    '''
    f = _FilterPlugins(obs=obs)
    return _download_plugin(repo_name, info_only=info_only, filter_cb=f.filter)

def install_plugin(filename):
    '''Install plugin
    :param filename:  Path to the plugin file, ZIP or PKG.
    '''
    return _install_plugin(filename)

def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--info-only', action='store_true', default=None,
                        help='Print the asset information and exit')
    parser.add_argument('--obs', action='store', default=None,
                        help='OBS Studio version')
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
            path = download_plugin(name, info_only=args.info_only, obs=args.obs)
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
