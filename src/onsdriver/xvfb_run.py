'''
Run Xvfb
'''

import tempfile
import os
import os.path
import subprocess
import sys

_SCREEN_RES = '1080x768x24'

_INST = None

def _find_free_servernum(num):
    def _exists(i):
        if os.path.exists(f'/tmp/.X{i}-lock'):
            return True
        if os.path.exists(f'/tmp/.X11-unix/X{i}'):
            return True
        return False
    while _exists(num):
        num -= 1
    return num

def _mcookie():
    res = subprocess.run(['mcookie', ], check=True, capture_output=True)
    return res.stdout.decode('ascii').strip()

def _xauth_add(num, proto='.', mcookie=None):
    if not mcookie:
        mcookie = _mcookie()
    subprocess.run(['xauth', 'add', f':{num}', proto, mcookie], check=True)

class XvfbRun:
    'Class to run xvfb'

    def __init__(self, start=True):
        self.d = None
        self.proc_xvfb = None
        if start:
            self.start()

    def __del__(self):
        self.cleanup()

    def start(self):
        'Start Xvfb'
        num = _find_free_servernum(99)
        self.d = tempfile.TemporaryDirectory(prefix='onsdriver-xvfb-') # pylint: disable=consider-using-with
        xauth = self.d.name + '/Xauthority'
        with open(xauth, 'w', encoding='ascii'):
            pass
        os.environ['XAUTHORITY'] = xauth

        sys.stderr.write(f'Starting Xvfb on :{num}...\n')
        self.proc_xvfb = subprocess.Popen( # pylint: disable=consider-using-with
                ['Xvfb', f':{num}', '-screen', '0', _SCREEN_RES, '-nolisten', 'tcp', ],
                stdout = subprocess.DEVNULL,
                stderr = subprocess.DEVNULL,
        )

        os.environ['DISPLAY'] = f':{num}'
        _xauth_add(num)

    def detatch(self):
        '''Detatch the existing run
        The temporary directory won't be removed.
        The process won't be killed at the end
        '''
        self.d = None
        self.proc_xvfb = None

    def cleanup(self):
        'Stop Xvfb'
        if self.proc_xvfb:
            self.proc_xvfb.terminate()
            try:
                self.proc_xvfb.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.proc_xvfb.kill()
                self.proc_xvfb.wait(timeout=3)
            self.proc_xvfb = None

        if self.d:
            self.d.cleanup()
            self.d = None

def xvfb_run():
    'Start Xvfb instance'

    # Xvfb process will be started only once for each script run.
    # The process will be terminated at the end of the script.
    global _INST # pylint: disable=global-statement
    if not _INST:
        _INST = XvfbRun()
    return _INST

def _get_args():
    import argparse # pylint: disable=import-outside-toplevel
    parser = argparse.ArgumentParser()
    return parser.parse_args()

def main():
    'Entry point'
    _ = _get_args()

    inst = XvfbRun()
    inst.detatch()
    for e in ('DISPLAY', 'XAUTHORITY'):
        print(f'{e}={os.environ[e]}')

if __name__ == '__main__':
    main()
