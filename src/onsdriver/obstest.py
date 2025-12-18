'''
Base class to run OBS Studio and test something
'''

import os
import os.path
import shutil
import unittest
from onsdriver import obsconfig, obsexec

class OBSTest(unittest.TestCase):
    'Base class to test with OBS Studio'
    def setUp(self, config_name='saved-config', run=True):
        cfg = obsconfig.OBSConfigCopyFromSaved(config_name)
        self.obs = obsexec.OBSExec(cfg, run=run)
        self.name = self.id() # .rsplit('.', 1)[-1]

    def tearDown(self):
        self.obs.shutdown()
        self.assertEqual(self.memory_leak(), 0)
        self.move_log(prefix=self.name+'-')

    def memory_leak(self):
        'Return the number of memory leak in the last log, or -1 if not found.'
        with open(self.obs.get_logfile(), encoding='utf-8') as fr:
            for l in fr:
                if 'Number of memory leaks:' in l:
                    return int(l.rsplit(' ', 1)[-1])
        return -1

    def move_log(self, prefix=''):
        '''Move the last log
        :param prefix:  The prefix of the destination file name.'
        '''
        src = self.obs.get_logfile()
        dst = prefix + os.path.basename(src).replace('-', '').replace(' ', '-')
        if not os.path.isabs(prefix):
            try:
                logsdir = os.environ['ONSDRIVER_LOGS']
            except KeyError:
                logsdir = 'logs'
            os.makedirs(logsdir, exist_ok=True)
            dst = logsdir + '/' + dst

        shutil.move(src, dst)
