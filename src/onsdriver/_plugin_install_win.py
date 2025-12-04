'Install plugin on Windows'

import os.path
import zipfile

from onsdriver import obsexec

_INSTALLED_WINDOWS_FILES = set()

def install_plugin_windows_zip(filename):
    '''
    Install a ZIP plugin for Windows.
    :param filename:  file name on this system.
    '''
    dirname = os.path.dirname(os.path.dirname(os.path.dirname(obsexec.get_exec_path())))

    with zipfile.ZipFile(filename) as z:
        z.extractall(dirname)
        for a in z.namelist():
            _INSTALLED_WINDOWS_FILES.add(dirname + '/' + a)
