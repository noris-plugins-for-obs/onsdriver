'''
This module provides useful functions when testing with obs-studio.
'''

import os.path
import time

class RetryAttempt:
    'Describes the contex of the attempt to retry'
    def __init__(self, count, error_msg):
        self.count = count
        self.error_msg = error_msg

    def __str__(self):
        if self.count <= 1:
            return f'{self.count} attempt'
        return f'{self.count} attempts'

    def increment(self):
        'Increment the count'
        self.count += 1
        return self

    def set_error(self, error_msg):
        '''Set the last error message
        This will be useful to describe the status of the last iteration.
        '''
        self.error_msg = error_msg

def retry(timeout, each_wait=0.1, error_msg=None):
    '''Retry until meeting a condition
    Use this function with `while` statement like below.
    for _ in retry(timeout=10):
        good = your_task()
        if good:
            break
    :param timeout:    Set the timeout in second
    :param each_wait:  Sleep time for each
    '''
    attempt = RetryAttempt(1, error_msg)
    yield attempt

    count = int(timeout // each_wait + 0.5)
    while count > 0:
        time.sleep(each_wait)
        yield attempt.increment()
        count -= 1

    raise TimeoutError(attempt.error_msg)

def ignore_directory(path):
    '''Create .gitignore file to ignore the directory
    :param path:  Path of the directory to be ignored
    '''
    ignore_path = f'{path}/.gitignore'
    if os.path.exists(ignore_path):
        return
    with open(ignore_path, 'w', encoding='ascii') as fw:
        fw.write('*\n')
