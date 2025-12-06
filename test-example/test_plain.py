'''
Plain test case for OBS Studio
'''

import time
import unittest
from onsdriver import obstest, obsui


class PlainTest(obstest.OBSTest):
    'Test plain features of OBS Studio'

    def test_nothing(self):
        'Just start and exit'
        time.sleep(1)

    def test_color_source(self):
        'Create color source'
        cl = self.obs.get_obsws()

        scene = 'Scene'
        name = 'Color Source'
        cl.send('CreateInput', {
            'inputName': name,
            'sceneName': scene,
            'inputKind': 'color_source_v3',
            'inputSettings': {
                'color': 0xFFD7CCC6,
                'width': 640,
                'height': 360,
            },
        })

        time.sleep(1)

        res = cl.send('GetSceneItemList', {'sceneName': scene})
        names = [item['sourceName'] for item in res.scene_items]
        self.assertIn(name, names)

        ui = obsui.OBSUI(cl)
        ui.grab(path=[], filename=f'screenshots/{self.name}-window.png', window=True)

        try:
            ui.grab(path=[], filename=f'screenshots/{self.name}-pillow.png', pillow=True)
        except (ImportError, OSError) as e:
            # ImportError: If Pillow is not installed, not raise error but just inform it.
            # OSError: X connection failed on Linux if DISPLAY is not set.
            print(e)


if __name__ == '__main__':
    unittest.main()
