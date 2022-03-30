"""Module containing the logic for UnrealDevice."""

import functools
from datetime import datetime

from gtunrealdevice.exceptions import WrapperError
from gtunrealdevice.exceptions import UnrealDeviceConnectionError
from gtunrealdevice.exceptions import UnrealDeviceOfflineError

from gtunrealdevice.core import DEVICES_DATA


def check_active_device(func):
    """Wrapper for URDevice methods.
    Parameters
    ----------
    func (function): a callable function

    Returns
    -------
    function: a wrapper function

    Raises
    ------
    WrapperError: raise exception when decorator is incorrectly used
    URDeviceOfflineError: raise exception when unreal device is offline
    """
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
        """A Wrapper Function"""
        if args:
            device = args[0]
            if isinstance(device, URDevice):
                if device.is_connected:
                    result = func(*args, **kwargs)
                    return result
                else:
                    fmt = '{} device is offline.'
                    raise UnrealDeviceOfflineError(fmt.format(device.name))
            else:
                fmt = 'Using invalid decorator for this instance "{}"'
                raise WrapperError(fmt.format(type(device)))
        else:
            raise WrapperError('Using invalid decorator')
    return wrapper_func


class URDevice:
    """Unreal Device class

    Attributes
    ----------
    address (str): an address of device
    name (str): name of device
    kwargs (dict): keyword arguments

    Properties
    ----------
    is_connected -> bool

    Methods
    -------
    connect(**kwargs) -> bool
    disconnect(**kwargs) -> bool
    execute(cmdline, **kwargs) -> str
    configure(config, **kwargs) -> str

    Raises
    ------
    URDeviceConnectionError: raise exception if device can not connect
    """
    def __init__(self, address, name='', **kwargs):
        self.address = str(address).strip()
        self.name = str(name).strip() or self.address
        self.__dict__.update(**kwargs)
        self._is_connected = False
        self.data = None
        self.table = dict()
        self.testcase = ''

    @property
    def is_connected(self):
        """Return device connection status"""
        return self._is_connected

    def connect(self, **kwargs):
        """Connect an unreal device

        Parameters
        ----------
        kwargs (dict): keyword arguments

        Returns
        -------
        bool: connection status
        """
        if self.is_connected:
            return self.is_connected

        if self.address in DEVICES_DATA:
            self.data = DEVICES_DATA.get(self.address)
            self._is_connected = True

            testcase = kwargs.get('testcase', '')
            if testcase:
                if testcase in self.data.get('testcases', dict()):
                    self.testcase = testcase
                else:
                    fmt = '*** "{}" test case is unavailable for this connection ***'
                    print(fmt.format(testcase))

            if kwargs.get('showed', True):
                login_result = self.data.get('login', '')
                if login_result:
                    is_timestamp = kwargs.get('is_timestamp', True)
                    login_result = self.render_data(
                        login_result, is_timestamp=is_timestamp
                    )
                    print(login_result)
            return self.is_connected
        else:
            fmt = '{} is unavailable for connection.'
            raise UnrealDeviceConnectionError(fmt.format(self.name))

    def disconnect(self, **kwargs):
        """Disconnect an unreal device

        Parameters
        ----------
        kwargs (dict): keyword arguments

        Returns
        -------
        bool: disconnection status
        """
        self._is_connected = False
        if kwargs.get('showed', True):
            is_timestamp = kwargs.get('is_timestamp', True)
            msg = '{} is disconnected.'.format(self.name)
            msg = self.render_data(msg, is_timestamp=is_timestamp)
            print(msg)
        return self._is_connected

    @check_active_device
    def execute(self, cmdline, **kwargs):
        """Execute command line for an unreal device

        Parameters
        ----------
        cmdline (str): command line
        kwargs (dict): keyword arguments

        Returns
        -------
        str: output of a command line
        """

        data = self.data.get('cmdlines')
        if self.testcase:
            data = self.data.get('testcases').get(self.testcase, data)

        no_output = '*** "{}" does not have output ***'.format(cmdline)
        result = data.get(cmdline, self.data.get('cmdlines').get(cmdline, no_output))
        if not isinstance(result, (list, tuple)):
            output = str(result)
        else:
            index = 0 if cmdline not in self.table else self.table.get(cmdline) + 1
            index = index % len(result)
            self.table.update({cmdline: index})
            output = result[index]

        is_timestamp = kwargs.get('is_timestamp', True)
        output = self.render_data(output, is_timestamp=is_timestamp)
        if kwargs.get('showed', True):
            print(output)
        return output

    @check_active_device
    def configure(self, config, **kwargs):
        """Configure an unreal device

        Parameters
        ----------
        config (str): configuration data for device
        kwargs (dict): keyword arguments

        Returns
        -------
        str: result of configuration
        """
        is_timestamp = kwargs.get('is_timestamp', True)
        result = self.render_data(config, is_cfg=True, is_timestamp=is_timestamp)
        if kwargs.get('showed', True):
            print(result)
        return result

    def render_data(self, data, is_cfg=False, is_timestamp=True):

        if isinstance(data, str):
            lst = data.splitlines()
        else:
            lst = []
            for item in data:
                if isinstance(item, str):
                    lst.extend(item.splitlines())
                else:
                    lst.extend(item)

        if is_cfg:
            prompt = '{}(configure)#'.format(self.name)

            for index, item in enumerate(lst):
                if index == 0:
                    continue
                lst[index] = '{} {}'.format(prompt, item)

        if is_timestamp:
            dt = datetime.now()
            fmt = '+++ {:%b %d %Y %T}.{} from "unreal-device" for "{}"'
            timestamp = fmt.format(dt, str(dt.microsecond)[:3], self.name)
            lst.insert(int(is_cfg), timestamp)

        result = '\n'.join(lst)
        return result
