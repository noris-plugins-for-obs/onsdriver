'''
Test filters in obsplugin module
'''

import unittest
from onsdriver import obsplugin

def _make_asset(name):
    return {
            'name': name,
    }

def _names(assets):
    return [a['name'] for a in assets]

class FilterPluginsByOBSVerTest(unittest.TestCase):
    'Class to test FilterPluginsByOBSVer'

    def test_version_filter(self):
        'Ensure incompatible assets are removed'
        assets = [
                _make_asset(name='plugin-0.1.0-obs28.zip'),
                _make_asset(name='plugin-0.1.0-obs30.zip'),
                _make_asset(name='plugin-0.1.0-obs30.1.zip'),
                _make_asset(name='plugin-0.1.0-obs31.zip'),
        ]

        res = obsplugin.FilterPluginsByOBSVer(obs='29.0.0').filter(assets)
        self.assertEqual(_names(res), _names(assets[0:1]))

        res = obsplugin.FilterPluginsByOBSVer(obs='30').filter(assets)
        self.assertEqual(_names(res), _names(assets[0:2]))

        res = obsplugin.FilterPluginsByOBSVer(obs='30.0.0').filter(assets)
        self.assertEqual(_names(res), _names(assets[0:2]))

        res = obsplugin.FilterPluginsByOBSVer(obs='30.0.1').filter(assets)
        self.assertEqual(_names(res), _names(assets[0:2]))

        res = obsplugin.FilterPluginsByOBSVer(obs='30.1.0').filter(assets)
        self.assertEqual(_names(res), _names(assets[0:3]))

        res = obsplugin.FilterPluginsByOBSVer().filter(assets)
        self.assertEqual(_names(res), _names(assets))

    def test_sort_stability(self):
        'Ensure the sort is stable'
        assets = [
                _make_asset(name='plugin-0.1.0-obs30-arch2.zip'),
                _make_asset(name='plugin-0.1.0-obs30-arch1.zip'),
                _make_asset(name='plugin-0.1.0-obs28.zip'),
        ]
        sorted_assets = assets[2:] + assets[0:2]

        res = obsplugin.FilterPluginsByOBSVer(obs='30.0.0').filter(assets)
        self.assertEqual(_names(res), _names(sorted_assets))

        res = obsplugin.FilterPluginsByOBSVer().filter(sorted_assets)
        self.assertEqual(_names(res), _names(sorted_assets))

if __name__ == '__main__':
    unittest.main()
