'Install plugin on macOS'

import os
import subprocess
import zipfile

def install_plugin_macos_zip(filename):
    '''
    Install a ZIP plugin for macOS.
    :param filename:  file name on this system.
    '''
    dirname = os.environ['HOME'] + '/Library/Application Support/obs-studio/plugins/'
    os.makedirs(dirname, exist_ok=True)

    with zipfile.ZipFile(filename) as z:
        z.extractall(dirname)

def install_plugin_macos_pkg(filename):
    '''
    Install a PKG plugin for macOS.
    :param filename:  file name on this system.
    '''
    dirname = os.environ['HOME'] + '/Library/Application Support/obs-studio/plugins/'
    os.makedirs(dirname, exist_ok=True)

    subprocess.run([
        'installer',
        '-pkg', filename,
        '-target', 'CurrentUserHomeDirectory',
        ], check=True)
