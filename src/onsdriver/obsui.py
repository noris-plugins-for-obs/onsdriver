'''
Communicate with ui-ws-automation plugin
'''

from time import sleep

_VENDOR_NAME = 'ui-ws-automation'

class OBSUI:
    'Communicate with ui-ws-automation plugin'
    # pylint: disable=too-few-public-methods

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
