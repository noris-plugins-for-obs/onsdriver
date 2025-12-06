'''
Communicate with ui-ws-automation plugin
'''

import base64
import os
import os.path
from time import sleep

_VENDOR_NAME = 'ui-ws-automation'

class OBSUI:
    'Communicate with ui-ws-automation plugin'

    def __init__(self, cl):
        self.cl = cl

    def _request(self, param, retry):
        res = self.cl.send('CallVendorRequest', param)
        if 'error' in res.response_data:
            error = res.response_data['error']
            if error == 'Error: no object found' and retry > 0:
                sleep(1)
                return self._request(param, retry - 1)
            raise OSError(error)
        return res.response_data

    def request(self, request_type, request_data, retry=3):
        'Invoke a request on ui-ws-automation'
        param = {
                'vendorName': _VENDOR_NAME,
                'requestType': request_type,
                'requestData': request_data,
        }
        return self._request(param, retry)

    def grab(self, path, window=False, filename=None):
        '''Request to get an image of a widget
        :param path:      List to describe the widget.
        :param window:    Boolean value to control grab type.
        :param filename:  File name to save the PNG file to. If given, None is returned.
        :return:          Bytes object representing PNG.
        '''
        s_type = 'window' if window else 'grab'
        res = self.request('widget-grab', {'path': path, 'type': s_type})
        png = base64.b64decode(res['image'])
        if filename:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as fw:
                fw.write(png)
            return None
        return png
