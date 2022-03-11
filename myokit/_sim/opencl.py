#
# OpenCL information class
#
# This file is part of Myokit.
# See http://myokit.org for copyright, sharing, and licensing details.
#
from __future__ import absolute_import, division
from __future__ import print_function, unicode_literals

import os
import myokit

try:
    # Python2
    from ConfigParser import ConfigParser
except ImportError:
    # Python 3
    from configparser import RawConfigParser as ConfigParser


# Settings file
SETTINGS_FILE = os.path.join(myokit.DIR_USER, 'preferred-opencl-device.ini')


# Location of C source for OpenCL info module
SOURCE_FILE = 'opencl.c'


class OpenCL(myokit.CModule):
    """
    Tests for OpenCL support and can return information about opencl
    simulations.
    """
    # Unique id for this object
    _index = 0

    # Cached back-end object if compiled, False if compilation failed
    _instance = None

    # Cached compilation error message
    _message = None

    def __init__(self):
        super(OpenCL, self).__init__()
        # Create back-end and cache it
        OpenCL._index += 1
        mname = 'myokit_opencl_info_' + str(OpenCL._index)
        mname += '_' + str(myokit.pid_hash())
        fname = os.path.join(myokit.DIR_CFUNC, SOURCE_FILE)
        args = {'module_name': mname}

        # Define libraries
        libs = []
        flags = []
        import platform
        if platform.system() != 'Darwin':   # pragma: no macos cover
            libs.append('OpenCL')
        else:                               # pragma: no cover
            flags.append('-framework')
            flags.append('OpenCL')

        # Add include / linker paths
        libd = list(myokit.OPENCL_LIB)
        incd = list(myokit.OPENCL_INC)
        incd.append(myokit.DIR_CFUNC)

        try:
            OpenCL._message = None
            OpenCL._instance = self._compile(
                mname, fname, args, libs, libd, incd, larg=flags)
        except myokit.CompilationError as e:    # pragma: no cover
            OpenCL._instance = False
            OpenCL._message = str(e)

    @staticmethod
    def _get_instance():
        """
        Returns a cached back-end, creates and returns a new back-end or raises
        a :class:`NoOpenCLError`.
        """
        # No instance? Create it
        if OpenCL._instance is None:
            OpenCL()
        # Instance creation failed, raise exception
        if OpenCL._instance is False:   # pragma: no cover
            raise NoOpenCLError(
                'OpenCL support not found.\n' + OpenCL._message)
        # Return instance
        return OpenCL._instance

    @staticmethod
    def available():
        """
        Returns ``True`` if OpenCL support has been detected on this sytem and
        at least one platform and device were detected.
        """
        try:
            info = OpenCL.info()
        except Exception:   # pragma: no cover
            return False
        for p in info.platforms:
            for d in p.devices:
                return True
        return False    # pragma: no cover

    @staticmethod
    def current_info(formatted=False):
        """
        Returns a :class:`myokit.OpenCLPlatformInfo` object for the platform
        and device selected by the user, or chosen as default.

        If ``formatted=True`` is set, a formatted version of the information is
        returned instead.
        """
        platform, device = OpenCL.load_selection_bytes()
        info = OpenCL._get_instance().current(platform, device)
        info = OpenCLPlatformInfo(info)
        return info.format() if formatted else info

    @staticmethod
    def info(formatted=False):
        """
        Queries the OpenCL installation for the available platforms and
        devices and returns a :class:`myokit.OpenCLInfo` object.

        If ``formatted=True`` is set, a formatted version of the information is
        returned instead.
        """
        if not OpenCL.supported():  # pragma: no cover
            if formatted:
                return 'No OpenCL support detected.'
            return OpenCLInfo()

        info = OpenCLInfo(OpenCL._get_instance().info())
        if formatted:
            if len(info.platforms) == 0:  # pragma: no cover
                return 'OpenCL drivers detected, but no devices found.'
            return info.format()
        return info

    @staticmethod
    def load_selection():
        """
        Loads a platform/device selection from disk and returns a tuple
        ``(platform, device)``. Each entry in the tuple is either a string
        with the platform/device name, or ``None`` if no preference was set.
        """
        platform, device = OpenCL.load_selection_bytes()
        if platform is not None:
            platform = platform.decode('ascii')
        if device is not None:
            device = device.decode('ascii')

        return platform, device

    @staticmethod
    def load_selection_bytes():
        """
        Loads a platform/device selection from disk and returns a tuple
        ``(platform, device)``. Each entry in the tuple is either a string
        with the platform/device name, or ``None`` if no preference was set.
        """
        platform = device = None

        # Read ini file
        inifile = os.path.expanduser(SETTINGS_FILE)
        if os.path.isfile(inifile):
            config = ConfigParser()
            try:
                config.read(inifile, encoding='ascii')  # Python 3
            except TypeError:   # pragma: no python 3 cover
                config.read(inifile)

            def get(section, option):
                x = None
                if config.has_section(section):
                    if config.has_option(section, option):
                        x = config.get(section, option).strip()
                        if x:
                            return x
                return None

            platform = get('selection', 'platform')
            device = get('selection', 'device')

        # Ensure platform and device are ascii compatible byte strings, or None
        if platform is not None:
            platform = platform.encode('ascii')
        if device is not None:
            device = device.encode('ascii')

        return platform, device

    @staticmethod
    def save_selection(platform=None, device=None):
        """
        Stores a platform/device selection to disk.

        Both platform and device are identified by their names.
        """
        # Make sure platform and device can be stored as ascii
        if platform:
            platform = platform.encode('ascii').decode('ascii')
        if device:
            device = device.encode('ascii').decode('ascii')

        # Create configuration
        config = ConfigParser()
        config.add_section('selection')
        if platform:
            config.set('selection', 'platform', platform)
        if device:
            config.set('selection', 'device', device)

        # Write configuration to ini file
        inifile = os.path.expanduser(SETTINGS_FILE)
        with open(inifile, 'w') as configfile:
            config.write(configfile)

    @staticmethod
    def selection_info():
        """
        Returns a list of platform/device combinations along with information
        allowing the user to select one.

        The returned output is a list of tuples, where each tuple has the form
        ``(platform_name, device_name, specs)``.

        A preferred device can be selected by passing one of the returned
        ``platform_name, device_name`` combinations to
        :meth:`OpenCL.set_preferred_device`.
        """
        devices = []
        for platform in OpenCL.info().platforms:
            for device in platform.devices:
                specs = clockspeed(device.clock)
                specs += ', ' + bytesize(device.globl) + ' global'
                specs += ', ' + bytesize(device.local) + ' local'
                specs += ', ' + bytesize(device.const) + ' const'
                devices.append((platform.name, device.name, specs))
        return devices

    @staticmethod
    def supported():
        """
        Returns ``True`` if OpenCL support has been detected on this system.
        """
        try:
            OpenCL._get_instance()
            return True
        except NoOpenCLError:       # pragma: no cover
            return False

    '''
    @staticmethod
    def test_build(code):
        """
        Tries building a kernel program on the currently selected platform and
        device and returns the compiler output.
        """
        try:
            cl = OpenCL._get_instance()
        except NoOpenCLError as e:
            return False

        # Get preferred platform/device combo from configuration file
        platform, device = myokit.OpenCL.load_selection_bytes()

        # Build and return
        return cl.build(platform, device, code)
    '''


class OpenCLInfo(object):
    """
    Represents information about the available OpenCL platforms and devices.

    Each ``OpenCLInfo`` object has a property ``platforms``, containing a tuple
    of :class:`OpenCLPlatformInfo` objects.

    ``OpenCLInfo`` objects are created and returned by :class:`myokit.OpenCL`.
    """
    def __init__(self, mcl_info=[]):
        # mcl_info is a python object returned by mcl_device_info (mcl.h)
        self.platforms = tuple([OpenCLPlatformInfo(x) for x in mcl_info])

    def format(self):
        """
        Returns a formatted string version of this object's information.
        """
        b = []
        for i, platform in enumerate(self.platforms):
            b.append('Platform ' + str(i))
            platform._format(b, pre=' ')
        return '\n'.join(b)


class OpenCLPlatformInfo(object):
    """
    Represents information about an OpenCL platform.

    An ``OpenCLPlatformInfo`` object has the following properties:

    ``name`` (string)
        This platform's name.
    ``vendor`` (string)
        The vendor of this platform.
    ``version`` (string)
        The OpenCL version supported by this platform.
    ``profile`` (string)
        The supported OpenCL profile of this platform.
    ``extensions`` (string)
        The available OpenCL extensions on this platform.
    ``devices`` (tuple)
        A tuple of device information objects for the devices available on
        this platform. This field may be ``None``, in which case ``device``
        will be set instead.
    ``device`` (OpenCLDeviceInfo)
        An information objects for the device selected by the user, or chosen
        as the default device. This field may be ``None``, in which case
        ``devices`` will be set instead.

    ``OpenCLPlatformInfo`` objects are created as part of a :class:`OpenCLInfo`
    objects, as returned by most OpenCL enabled parts of Myokit.
    """
    def __init__(self, platform):
        self.name = platform['name'].strip()
        self.vendor = platform['vendor'].strip()
        self.version = platform['version'].strip()
        self.profile = platform['profile'].strip()
        self.extensions = platform['extensions'].strip().split()
        self.devices = platform.get('devices', None)
        if self.devices is not None:
            self.devices = tuple([OpenCLDeviceInfo(x) for x in self.devices])
        self.device = platform.get('device', None)
        if self.device is not None:
            self.device = OpenCLDeviceInfo(self.device)

    def format(self):
        """
        Returns a formatted string version of this object's information.
        """
        b = []
        b.append('Platform: ' + self.name)
        self._format(b, ' ', name=False)
        return '\n'.join(b)

    def _format(self, b, pre='', name=True):
        """
        Formats the information in this object and adds it to the list ``b``.
        """
        if name:
            b.append(pre + 'Name       : ' + self.name)
        b.append(pre + 'Vendor     : ' + self.vendor)
        b.append(pre + 'Version    : ' + self.version)
        b.append(pre + 'Profile    : ' + self.profile)
        b.append(pre + 'Extensions : ' + ' '.join(self.extensions))
        if self.devices is not None:
            b.append(pre + 'Devices:')
            for j, device in enumerate(self.devices):
                b.append(pre + ' Device ' + str(j))
                device._format(b, pre + '  ')

        if self.device is not None:
            b.append(pre[:-1] + 'Device: ' + self.device.name)
            self.device._format(b, pre, name=False)

    def has_extension(self, extension):
        return extension in self.extensions


class OpenCLDeviceInfo(object):
    """
    Represents information about an OpenCL device.

    An ``OpenCLDeviceInfo`` object has the following properties:

    ``name`` (string)
        This device's name.
    ``vendor`` (string)
        This device's vendor.
    ``version`` (string)
        The OpenCL version supported by this device.
    ``driver`` (string)
        The driver version for this device.
    ``clock`` (int)
        This device's clock speed (in MHz).
    ``globl`` (int)
        The available global memory on this device (in bytes).
    ``local`` (int)
        The available local memory on this device (in bytes).
    ``const`` (int)
        The available constant memory on this device (in bytes).
    ``units`` (int)
        The number of computing units on this device.
    ``param`` (int)
        The maximum total size (in bytes) of arguments passed to the
        kernel. This limits the number of arguments a kernel can get.
    ``groups`` (int)
        The maximum work group size.
    ``dimensions`` (int)
        The maximum work item dimension.
    ``items`` (tuple)
        A tuple of ints specifying the maximum work item size in each
        dimension.

    ``OpenCLDeviceInfo`` objects are created as part of a :class:`OpenCLInfo`
    objects, as returned by most OpenCL enabled parts of Myokit.
    """
    def __init__(self, device):
        self.name = device['name'].strip()
        self.vendor = device['vendor'].strip()
        self.version = device['version'].strip()
        self.driver = device['driver'].strip()
        self.clock = device['clock']
        self.globl = device['global']
        self.local = device['local']
        self.const = device['const']
        self.param = device['param']
        self.groups = device['groups']
        self.items = tuple(device['items'])

    def _format(self, b, pre='', name=True):
        """
        Formats the information in this object and adds it to the list ``b``.
        """
        if name:
            b.append(pre + 'Name            : ' + self.name)
        b.append(pre + 'Vendor          : ' + self.vendor)
        b.append(pre + 'Version         : ' + self.version)
        b.append(pre + 'Driver          : ' + self.driver)
        b.append(pre + 'Clock speed     : ' + str(self.clock) + ' MHz')
        b.append(pre + 'Global memory   : ' + bytesize(self.globl))
        b.append(pre + 'Local memory    : ' + bytesize(self.local))
        b.append(pre + 'Constant memory : ' + bytesize(self.const))
        b.append(pre + 'Max param size  : ' + str(self.param) + ' bytes')
        b.append(pre + 'Max work groups : ' + str(self.groups))
        b.append(pre + 'Max work items  : [' +
                 ', '.join([str(x) for x in self.items]) + ']')


def r(x):
    """Round x, convert to int if possible, the convert to string."""
    return str(myokit.float.round(round(x, 2)))


def bytesize(size):
    """
    Returns a formatted version of a ``size`` given in bytes.
    """
    # Format a size
    if size >= 1073741824:
        return r(0.1 * int(10 * (float(size) / 1073741824))) + ' GB'
    elif size >= 1048576:
        return r(0.1 * int(10 * (float(size) / 1048576))) + ' MB'
    elif size >= 1024:
        return r(0.1 * int(10 * (float(size) / 1024))) + ' KB'
    else:
        return str(size) + ' B'


def clockspeed(speed):
    """
    Returns a formatted version of a ``speed`` given in MHz.
    """
    # Format a size
    if speed >= 1000:
        return r(0.1 * int(10 * (float(speed) / 1000))) + ' GHz'
    else:
        return r(speed) + ' MHz'


class NoOpenCLError(myokit.MyokitError):
    """
    Raised when OpenCLInfo functions requiring OpenCL are called but no OpenCL
    support can be detected.
    """

