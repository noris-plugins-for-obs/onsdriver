'''
This module provides a functionality to execute obs-studio.
'''

import os
import os.path
import re
import sys
import subprocess
import tempfile
import time
import obsws_python
from onsdriver import obsconfig, obsui

_WAIVED_ERRORS_RE_LIST = (
    r'error: Failed to rename basic scene collection file:', # first time
    r'error: Tried to call obs_frontend_remove_event_callback with no callbacks!', # obs-websocket
    r'error: glBindFramebuffer failed, glGetError returned GL_INVALID_OPERATION', # random
    r'error: \[mac-virtualcam\] mac-camera-extension: OSSystemExtensionErrorCode 2',
    r'error: os_dlopen.*VLC.app',
    r'error: Crash sentinel location .* unable to create directory', # first time on Windows
)

_WAIVED_ERRORS_RE = re.compile('(' + '|'.join(_WAIVED_ERRORS_RE_LIST) + ')')

def _normalize_exec_path(path):
    if sys.platform == 'darwin':
        candidates = (
                path + '/Contents/MacOS/OBS',
                path,
        )
    elif sys.platform == 'win32':
        candidates = (
                path + '/bin/64bit/obs64.exe',
                path,
        )
    else:
        return path
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return None

def get_exec_path():
    'Return the executable file path of OBS'
    if 'OBS_EXEC' in os.environ:
        return _normalize_exec_path(os.environ['OBS_EXEC'])
    if sys.platform == 'linux':
        return 'obs'
    if sys.platform == 'darwin':
        paths = (
                'obs-studio/OBS.app',
                'obs-studio/build_macos/frontend/RelWithDebInfo/OBS.app',
                '../obs-studio/build_macos/frontend/RelWithDebInfo/OBS.app',
        )
    elif sys.platform == 'win32':
        paths = (
                'obs-studio',
                '../obs-studio',
        )
    else:
        raise NotImplementedError(f'Not supported platform: {sys.platform}')

    for path in paths:
        path = _normalize_exec_path(path)
        if os.path.isfile(path):
            return os.path.abspath(path)

    raise ValueError(f'Cannot find obs-studio executable path for {sys.platform}')

class OBSExec:
    'Class to run OBS Studio'
    def __init__(self, config=None, run=True, exec_path=None, enable_obsws=True):
        if not config:
            config = obsconfig.OBSConfig()

        if exec_path:
            self.exec_path = _normalize_exec_path(exec_path)
        else:
            self.exec_path = get_exec_path()

        self.config = config
        self.proc_obs = None
        self._obsws = None
        self._tmp_stderr = None

        if enable_obsws:
            config.enable_obsws()
        if run:
            self.run()

    def run(self):
        'Start OBS Studio'
        self._obsws = None

        self.config.remove_logs()

        if sys.platform == 'linux':
            proc_cwd = None
            cmd = [self.exec_path]
            if 'DISPLAY' not in os.environ or not os.environ['DISPLAY']:
                cmd = ['xvfb-run', '-s', '-screen 0 1080x768x24'] + cmd
        elif sys.platform == 'win32':
            proc_cwd = os.path.dirname(self.exec_path)
            cmd = [os.path.abspath(self.exec_path)]
        else:
            proc_cwd = None
            cmd = [self.exec_path]

        # pylint: disable=consider-using-with
        self._tmp_stderr = tempfile.TemporaryFile()
        self.proc_obs = subprocess.Popen(
                cmd,
                stdout = subprocess.DEVNULL,
                stderr = self._tmp_stderr,
                cwd = proc_cwd,
        )

        # Wait startup
        # macos: Sometimes mac-avcapture-legacy takes 5 seconds.
        time.sleep(0.2)
        retry = 100
        while retry > 0 and not self._obs_started():
            time.sleep(0.1)
            retry -= 1

        cfg = self.config.get_obsws_cfg()
        if 'server_enabled' in cfg and cfg['server_enabled']:
            cl = self.get_obsws()
            ui = obsui.OBSUI(cl)

            # Ensure the main window is visible,
            # If not, ie. websocket request goes too early, UI will be corrupted.
            retry += 1
            while retry > 0:
                res = ui.request('widget-list', {})
                if res['visible']:
                    break
                time.sleep(0.1)
                retry -= 1

    def _get_obsws_passwd(self):
        cfg = self.config.get_obsws_cfg()
        try:
            if cfg['auth_required']:
                return cfg['server_password']
            return None
        except KeyError:
            return None

    def get_obsws(self, use_cache=True):
        '''Return an instance of obsws_python.ReqClient

        :param use_cache:  If true, try to return a cached instance.
        '''
        if use_cache:
            try:
                if self._obsws and not self._obsws.base_client.ws.connected:
                    self._obsws = None
            except: # pylint: disable=bare-except
                pass

            if self._obsws:
                return self._obsws

        n_retry = 10
        err = None
        while n_retry > 0:
            n_retry -= 1
            try:
                pw = self._get_obsws_passwd()
                self._obsws = obsws_python.ReqClient(host='localhost', port=4455, password=pw)
                if sys.platform == 'linux' and n_retry != 9:
                    print(f'Info: Succeeded to connect websocket after {8 - n_retry} attempt(s).')
                    sys.stdout.flush()
                return self._obsws
            except ConnectionRefusedError as e:
                err = e
                if self.proc_obs and self.proc_obs.poll() is None:
                    time.sleep(3)
                    if n_retry < 7:
                        print(f'Info: Failed to connect websocket {e=}. {n_retry} more attempt(s).')
                        sys.stdout.flush()
        raise err

    def close_ws(self):
        'Close the last websocket client to prepare shutdown'
        if self._obsws:
            self._obsws.disconnect()
            self._obsws = None

    def get_logfile(self):
        'Return the latest log file path'
        logsdir = self.config.path + '/logs/'
        logs = os.listdir(logsdir)
        if not logs:
            return None
        return logsdir + max(logs)

    def _obs_started(self):
        try:
            log = self.get_logfile()
            if not log:
                return False
            with open(log, 'r', encoding='utf-8') as fr:
                for line in fr:
                    if 'Switched to scene' in line:
                        return True
        except FileNotFoundError:
            pass
        return False

    def shutdown(self, wait=True):
        'Shutdown OBS Studio'
        cl = self.get_obsws()
        res = cl.send('CallVendorRequest', {
            'vendorName': 'obs-shutdown-plugin',
            'requestType': 'shutdown',
            'requestData': {
                'reason': f'requested through onsdriver by {sys.argv[0]}',
                'support_url': 'https://github.com/noris-plugins-for-obs/onsdriver/issues',
                'force': True,
                'exit_timeout': 5.0,
            }
        })
        if res.response_data != {}:
            raise ValueError(f'shutdown request returned {res.response_data}')
        del cl
        if wait:
            return self.wait()
        return None

    def wait(self, check_error=True):
        'Wait OBS to exit'
        self.close_ws()

        exit_code = self.proc_obs.wait()
        if exit_code != 0:
            raise OSError(f'OBS exit with code {exit_code}')

        if self._tmp_stderr:
            self._tmp_stderr.seek(0)
            has_error = False
            for line in self._tmp_stderr.read().decode('utf-8').split('\n'):
                if _WAIVED_ERRORS_RE.match(line):
                    continue
                if line.startswith('error: '):
                    has_error = True
                    sys.stderr.write(line + '\n')
            self._tmp_stderr.close()
            self._tmp_stderr = None
            if has_error and check_error:
                raise OSError('OBS has error in log.')
