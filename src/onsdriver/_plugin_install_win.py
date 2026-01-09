'Install plugin on Windows'

import os
import os.path
import re
import subprocess
import zipfile

from onsdriver import obsexec

_RE_TYPE_LEGACY = re.compile(r'obs-plugins/[0-9]*bit/[^/]*\.dll')
_RE_TYPE_PROGRAMDATA = re.compile(r'[^/]*/bin/[0-9]*bit/[^/]*\.dll')

_INSTALLED_WINDOWS_FILES = set()

def _get_obs_dir_name():
    return os.path.dirname(os.path.dirname(os.path.dirname(obsexec.get_exec_path())))

def _is_legacy_type(z):
    for f in z.namelist():
        if _RE_TYPE_LEGACY.match(f):
            return True
    return False

def _is_programdata_type(z):
    for f in z.namelist():
        if _RE_TYPE_PROGRAMDATA.match(f):
            return True
    return False

def install_plugin_windows_zip(filename):
    '''
    Install a ZIP plugin for Windows.
    :param filename:  file name on this system.
    '''

    with zipfile.ZipFile(filename) as z:
        if _is_legacy_type(z):
            dirname = _get_obs_dir_name()
        elif _is_programdata_type(z):
            dirname = os.environ["ProgramData"] + '/obs-studio/plugins'
        else:
            raise ValueError(f'Unknown ZIP file type: {filename}')

        z.extractall(dirname)
        for a in z.namelist():
            _INSTALLED_WINDOWS_FILES.add(dirname + '/' + a)

def install_plugin_windows_exe(filename):
    '''
    Install an EXE plugin for Windows.
    :param filename:  file name on this system.
    '''

    cmd = [
            filename,
            '/verysilent',
    ]
    subprocess.run(cmd, check=True)
