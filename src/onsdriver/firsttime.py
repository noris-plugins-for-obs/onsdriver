'''
Run the first-time wizard and configure OBS Studio
'''

import argparse
import base64
import os
import shutil
from onsdriver import obsconfig, obsplugin, obsexec, obsui

_REQUIRED_PLUGIN_URLS = (
        'https://github.com/noris-plugins-for-obs/ui-ws-automation',
        'https://github.com/noris-plugins-for-obs/shutdown-plugin',
)

def _download_plugins(additional_plugins, info_only=False):
    ret = []

    for plugin in _REQUIRED_PLUGIN_URLS:
        ret.append(obsplugin.download_plugin(plugin, info_only=info_only))

    if additional_plugins:
        for plugin in additional_plugins:
            if plugin.startswith('http://') or plugin.startswith('https://'):
                ret.append(obsplugin.download_plugin(plugin, info_only=info_only))
            else:
                ret.append(plugin)

    return ret

def _prepare_config(additional_plugins):
    cfg = obsconfig.OBSConfig()
    cfg.remove_files()
    cfg.get_global_cfg('General')['EnableAutoUpdates'] = 'false'
    cfg.get_global_cfg('General')['MacOSPermissionsDialogLastShown'] = '65535'
    cfg.save_global_cfg()

    for path in _download_plugins(additional_plugins=additional_plugins):
        obsplugin.install_plugin(path)

    return cfg

def _run_obs(cfg, grab_png):
    obs = obsexec.OBSExec(config=cfg, run=True)

    ui = obsui.OBSUI(obs.get_obsws())
    try:
        ui.request('widget-invoke', {
            'path': [
                {"className": "AutoConfig"},
                {"className": "QWidget"},
                {"className": "QFrame"},
                {"className": "AutoConfigStartPage"},
                {"text": "I will only be using the virtual camera"},
            ],
            'method': 'click'
        })
        ui.request('widget-invoke', {
            'path': [
                {"className": "AutoConfig"},
                {"className": "QWidget"},
                {"className": "QPushButton", "enabled": True, "text": "Next"},
            ],
            'method': 'click'
        })
        ui.request('widget-invoke', {
            'path': [
                {"className": "AutoConfig"},
                {"className": "QWidget"},
                {"className": "QPushButton", "enabled": True, "objectName": "qt_wizard_finish"},
            ],
            'method': 'click'
        })
    except OSError:
        # If error happens, for example by translation, cancel the wizard.
        ui.request('widget-invoke', {
            'path': [
                {"className": "AutoConfig"},
                {"className": "QWidget"},
                {"className": "QPushButton", "enabled": True, "objectName": "qt_wizard_cancel"},
            ],
            'method': 'click'
        })

    if grab_png:
        res = ui.request('widget-grab', {
            "type": "window",
            'path': [],
        })
        png = base64.b64decode(res['image'])
        with open(grab_png, "wb") as fw:
            fw.write(png)

    obs.shutdown()

def _move_logs(cfg, dstdir, prefix):
    os.makedirs(dstdir, exist_ok=True)
    logsdir = cfg.path + '/logs/'
    for f in os.listdir(logsdir):
        dst = dstdir + '/' + prefix + f.replace('-', '').replace(' ', '-')
        shutil.move(logsdir+f, dst)

def run_firsttime(
        # pylint: disable=too-many-arguments
        *, configure=True, run=True, lang=None, additional_plugins=None, size=None, save_dst=None,
        grab_png=None, logs=None):
    '''Run the first time wizard and configure
    '''
    if configure:
        cfg = _prepare_config(additional_plugins=additional_plugins)
    else:
        cfg = obsconfig.OBSConfig()

    if run:
        try:
            _run_obs(cfg, grab_png=grab_png)
        finally:
            if logs:
                _move_logs(cfg, logs, prefix='firsttime-')

    cfg = obsconfig.OBSConfig()

    cfg.get_user_cfg('General')['Language'] = lang or 'en-US'
    cfg.save_user_cfg()

    if size:
        if len(size) == 2:
            size = size + size
        profile = cfg.get_profile()
        profile['Video']['BaseCX'] = str(size[0])
        profile['Video']['BaseCY'] = str(size[1])
        profile['Video']['OutputCX'] = str(size[2])
        profile['Video']['OutputCY'] = str(size[3])
        profile.save()


    if save_dst:
        cfg.save(dst_path=save_dst)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configure', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--plugins', nargs='+', default=[],
                        help='Also installs specified plugins.')
    parser.add_argument('--info-only', action='store_true', default=None,
                        help='Print the asset information and exit')
    parser.add_argument('--run', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--save', action='store', default=None,
                        help='Path to save the configuration directory')
    parser.add_argument('--grab', action='store', default=None,
                        help='Grab window and save as PNG')
    parser.add_argument('--run-again', action=argparse.BooleanOptionalAction, default=False,
                        help='After the first time run, starts OBS again.')
    parser.add_argument('--language', action='store', default=None,
                        help='Set the language code, default en-US')
    parser.add_argument('--size', action='store', default=None,
                        help='Set Base size and output size')
    parser.add_argument('--logs', action='store', default=None,
                        help='Move log file to the specified directory')
    args = parser.parse_args()

    if args.size:
        args.size = args.size.replace('x',':').split(':')

    return args

def main():
    'Entry point'
    args = _get_args()

    if args.info_only:
        paths = _download_plugins(
            additional_plugins = args.plugins,
            info_only=True
        )
        for path in paths:
            print(path)
        return

    run_firsttime(
            configure = args.configure,
            run = args.run,
            lang = args.language,
            additional_plugins = args.plugins,
            save_dst = args.save,
            size = args.size,
            grab_png = args.grab,
            logs = args.logs,
    )

    if args.run_again:
        try:
            obs = obsexec.OBSExec(run=True)
            obs.wait()
        finally:
            if args.logs:
                _move_logs(obs.config, dstdir=args.logs, prefix='firsttime-again-')

if __name__ == '__main__':
    main()
