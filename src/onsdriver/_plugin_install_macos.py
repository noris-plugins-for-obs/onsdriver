'Install plugin on macOS'

import os
import subprocess
import tempfile
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

    # The command 'sudo installer -pkg filename -target $HOME' cannot install to home but root.
    with tempfile.NamedTemporaryFile(suffix='.cpio') as t:
        res = subprocess.run(['7z', 'x', '-so', filename], check=True, capture_output=True)
        t.file.write(res.stdout)
        t.file.close()

        subprocess.run(['7z', 'x', '-o'+os.environ['HOME'], t.name], check=True)
