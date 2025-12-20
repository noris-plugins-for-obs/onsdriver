'''
This module provides configuration directory access to test obs-studio.
'''

import configparser
import os
import os.path
import random
import shutil
import string
import sys
import tempfile
import json
import copy

_OBSWS_CONFIG_PATH = '/plugin_config/obs-websocket/config.json'

def _get_config_dir():
    if sys.platform == 'linux':
        try:
            return os.environ['XDG_CONFIG_HOME'] + '/obs-studio'
        except KeyError:
            return os.environ['HOME'] + '/.config/obs-studio'
    elif sys.platform == 'darwin':
        return os.environ['HOME'] + '/Library/Application Support/obs-studio'
    elif sys.platform == 'win32':
        return os.environ['AppData'] + '/obs-studio'
    else:
        raise NotImplementedError(f'Not supported platform: f{sys.platform}')

def _generate_password():
    cand = string.ascii_lowercase + string.digits + string.ascii_uppercase
    return ''.join([random.choice(cand) for i in range(0, 16)])


class TemporaryConfigContext:
    '''
    Backup the configuration directory and revert it
    '''

    def __init__(self):
        self.backup_dir = None
        self.config_not_found = False
        self._need_restore = False

    def backup(self):
        'Backup the config directory'
        if self.backup_dir:
            raise ValueError(f'Backup "{self.backup_dir}" exists')
        cfg_dir = _get_config_dir()
        backup_dir = tempfile.mkdtemp(prefix='onsdriver-backup-', dir=os.path.dirname(cfg_dir))
        if os.path.exists(cfg_dir):
            shutil.move(cfg_dir, backup_dir)
        else:
            self.config_not_found = True
        self._need_restore = True
        self.backup_dir = backup_dir

    def restore(self):
        'Restore the backed-up config directory'
        if not self._need_restore or not self.backup_dir:
            return
        self._need_restore = False
        cfg_dir = _get_config_dir()
        if os.path.exists(cfg_dir):
            shutil.move(cfg_dir, self.backup_dir + '/restoring')
        if not self.config_not_found:
            shutil.move(self.backup_dir + '/' + os.path.basename(cfg_dir), cfg_dir)
        self.backup_dir = None

    def __enter__(self):
        self.backup()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.restore()

    def __del__(self):
        self.restore()


class OBSProfile:
    '''
    Access a profile
    '''
    def __init__(self, path=None):
        self.path = path
        self._basic_cfg = None

    @property
    def basic(self):
        '''
        Get a config instance for 'basic.ini'
        '''
        if self._basic_cfg:
            return self._basic_cfg
        self._basic_cfg = configparser.RawConfigParser()
        self._basic_cfg.optionxform = lambda option: option
        self._basic_cfg.read(self.path + '/basic.ini', 'utf-8-sig')
        return self._basic_cfg

    def __getitem__(self, section):
        if section not in self.basic:
            self.basic.add_section(section)
        return self.basic[section]

    def save(self):
        'Save the updated config to basic.ini'
        with open(self.path + '/basic.ini', 'w', encoding='utf-8') as fw:
            self.basic.write(fw, space_around_delimiters=False)


class OBSConfig:
    '''
    Base class to access configuration directory for obs-studio.
    '''
    def __init__(self):
        self.path = _get_config_dir()
        self._global_cfg = None
        self._user_cfg = None

    def save(self, dst_path):
        '''
        Save the current state
        :param dst_path:  The path to save the state into.
        '''
        shutil.rmtree(dst_path, ignore_errors=True)
        shutil.copytree(self.path + '/', dst_path, symlinks=True)

    def get_global_cfg(self, section):
        'Return the global configuration'
        if not self._global_cfg:
            self._global_cfg = configparser.RawConfigParser()
            self._global_cfg.optionxform = lambda option: option
            self._global_cfg.read(self.path + '/global.ini', 'utf-8-sig')

        if section not in self._global_cfg:
            self._global_cfg.add_section(section)
        return self._global_cfg[section]

    def save_global_cfg(self):
        '''Save the global configuration
        Before using this method, use `get_global_cfg()` to update the config.
        '''
        if not self._global_cfg:
            return
        os.makedirs(self.path, mode=0o755, exist_ok=True)
        with open(self.path + '/global.ini', 'w', encoding='utf-8') as f:
            self._global_cfg.write(f, space_around_delimiters=False)

    def get_user_cfg(self, section):
        'Return the user configuration'
        if not self._user_cfg:
            self._user_cfg = configparser.RawConfigParser()
            self._user_cfg.optionxform = lambda option: option
            self._user_cfg.read(self.path + '/user.ini', 'utf-8-sig')

        if section not in self._user_cfg:
            self._user_cfg.add_section(section)
        return self._user_cfg[section]

    def save_user_cfg(self):
        'Save the user configuration'
        if not self._user_cfg:
            return
        os.makedirs(self.path, mode=0o755, exist_ok=True)
        with open(self.path + '/user.ini', 'w', encoding='utf-8') as f:
            self._user_cfg.write(f, space_around_delimiters=False)

    def get_last_version(self):
        '''Get the last OBS Studio version
        :return:  Tuple of major, minor, and patch version numbers
        '''
        version_int = int(self.get_global_cfg('General')['LastVersion'])
        major = version_int >> 24
        minor = (version_int >> 16) & 0xFF
        patch = version_int & 0xFFFF
        return (major, minor, patch)

    def get_profile(self, name=None):
        '''Get the profile object
        :param name:  Name of the profile. If not given, the default is selected.
        :return:      OBSProfile instance.
        '''
        if not name:
            if self.get_last_version() < (31, 0, 0):
                name = self.get_global_cfg('Basic')['ProfileDir']
            else:
                name = self.get_user_cfg('Basic')['ProfileDir']
        return OBSProfile(self.path + '/basic/profiles/' + name)

    def get_scenecollection_file(self, name=None):
        '''Get the scene-collection file path
        :param name:  Name of the profile. If not given, the default is selected.
        :return:      Scene collection JSON file path.
        '''
        if name:
            return f'{self.path}/basic/scenes/{name}.json'
        if self.get_last_version() < (31, 0, 0):
            fname = self.get_global_cfg('Basic')['SceneCollectionFile']
        else:
            fname = self.get_user_cfg('Basic')['SceneCollectionFile']
        return f'{self.path}/basic/scenes/{fname}'

    def get_obsws_cfg(self):
        'Return obsws config data'
        try:
            with open(self.path + _OBSWS_CONFIG_PATH, 'r', encoding='utf-8') as fr:
                return json.load(fr)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            return {}

    def enable_obsws(self, auth_required=True):
        'Enable websocket'
        config_obsws = self.get_obsws_cfg()
        orig = copy.deepcopy(config_obsws)
        config_obsws['first_load'] = False
        config_obsws['server_enabled'] = True
        config_obsws['server_port'] = 4455
        config_obsws['alerts_enabled'] = False
        config_obsws['auth_required'] = bool(auth_required)
        if auth_required:
            config_obsws['server_password'] = _generate_password()
        if config_obsws != orig:
            os.makedirs(os.path.dirname(self.path + _OBSWS_CONFIG_PATH), mode=0o755, exist_ok=True)
            with open(self.path + _OBSWS_CONFIG_PATH, 'w', encoding='utf-8') as fw:
                json.dump(config_obsws, fw)

    def remove_files(self):
        'Remove configuration files'
        shutil.rmtree(self.path, ignore_errors=True)

    def remove_logs(self):
        'Remove configuration files'
        shutil.rmtree(self.path + '/logs', ignore_errors=True)

class OBSConfigCopyFromSaved(OBSConfig):
    '''
    Restores from a saved configuration and prepare to start obs-studio.
    '''
    def __init__(self, src_path):
        OBSConfig.__init__(self)
        self.remove_files()
        os.makedirs(os.path.dirname(self.path), mode=0o755, exist_ok=True)
        shutil.copytree(src_path + '/', self.path, symlinks=True)
