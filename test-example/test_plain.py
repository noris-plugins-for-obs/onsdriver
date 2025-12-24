'''
Plain test case for OBS Studio
'''

import time
import unittest
from onsdriver import obstest


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

        res = cl.send('GetSceneItemList', {'sceneName': scene})
        names = [item['sourceName'] for item in res.scene_items]
        self.assertIn(name, names)


if __name__ == '__main__':
    unittest.main()
