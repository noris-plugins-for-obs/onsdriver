'''
Run the first-time wizard and configure OBS Studio
'''

import argparse
import base64
from onsdriver import obsconfig, obsplugin, obsexec, obsui

_REQUIRED_PLUGIN_URLS = (
        'https://github.com/noris-plugins-for-obs/ui-ws-automation',
        'https://github.com/noris-plugins-for-obs/shutdown-plugin',
)

def _prepare_config(additional_plugins, lang):
    cfg = obsconfig.OBSConfig()
    cfg.remove_files()
    cfg.get_global_cfg('General')['EnableAutoUpdates'] = 'false'
    cfg.get_global_cfg('General')['MacOSPermissionsDialogLastShown'] = '65535'
    cfg.save_global_cfg()

    cfg.get_user_cfg('General')['Language'] = lang or 'en-US'
    cfg.save_user_cfg()

    for plugin in _REQUIRED_PLUGIN_URLS:
        obsplugin.install_plugin(obsplugin.download_plugin(plugin))

    if additional_plugins:
        for plugin in additional_plugins:
            if plugin.startswith('https://'):
                obsplugin.install_plugin(obsplugin.download_plugin(plugin))
            else:
                obsplugin.install_plugin(plugin)

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


def run_firsttime(
        # pylint: disable=too-many-arguments
        *, configure=True, run=True, lang=None, additional_plugins=None, save_dst=None,
        grab_png=None):
    '''Run the first time wizard and configure
    '''
    if configure:
        cfg = _prepare_config(additional_plugins=additional_plugins, lang=lang)
    else:
        cfg = obsconfig.OBSConfig()

    if run:
        _run_obs(cfg, grab_png=grab_png)

    if save_dst:
        cfg.save(dst_path=save_dst)


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configure', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--run', action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument('--save', action='store', default=None,
                        help='Path to save the configuration directory')
    parser.add_argument('--grab', action='store', default=None,
                        help='Grab window and save as PNG')
    parser.add_argument('--run-again', action=argparse.BooleanOptionalAction, default=False,
                        help='After the first time run, starts OBS again.')
    parser.add_argument('--language', action='store', default=None,
                        help='Set the language code, default en-US')
    parser.add_argument('--plugins', nargs='+', default=[],
                        help='Also installs specified plugins.')
    args = parser.parse_args()
    return args

def main():
    'Entry point'
    args = _get_args()
    run_firsttime(
            configure = args.configure,
            run = args.run,
            lang = args.language,
            additional_plugins = args.plugins,
            save_dst = args.save,
            grab_png = args.grab,
    )

    if args.run_again:
        obs = obsexec.OBSExec(run=True)
        obs.wait()

if __name__ == '__main__':
    main()
