'''
Communicate with ui-ws-automation plugin
'''

import base64
import os
import os.path
from time import sleep

_VENDOR_NAME = 'ui-ws-automation'

def _obj_match(obj, cond):
    for key, value in cond.items():
        if key not in obj:
            return False
        if obj[key] != value:
            return False
    return True

def _find_object(objs, children_key, path, i_path=0):
    for child in objs[children_key]:
        if not _obj_match(child, path[i_path]):
            continue
        if i_path + 1 == len(path):
            return child
        ret = _find_object(child, children_key, path, i_path=i_path+1)
        if ret:
            return ret
    return None

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

    def menu_list(self, path=None):
        'Return a list of menu actions'
        res = self.request('menu-list', {})
        if not path:
            return res
        return _find_object(res, 'menu', path)

    def widget_list(self, path=None):
        'Return a list of widgets'
        res = self.request('widget-list', {})
        if not path:
            return res
        return _find_object(res, 'children', path)

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
