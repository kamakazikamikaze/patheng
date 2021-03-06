from binascii import hexlify, unhexlify
from datetime import datetime
from dateutil import tz
import json
import os
import sys
from importlib import import_module
from inspect import getargspec
from functools import wraps


def pinghost(host):
    """
    Ping target with a 1-second timeout limit

    :param str host: Destination to reach. IP address or domain name
    :returns: True if reached, otherwise False
    """
    host = str(host).split(':')[0]  # leave off the port if exists
    # print "Pinging"
    if os.name == 'posix':
        target = "ping -W1 -c 1 " + host + " > /dev/null 2>&1 "
    else:
        target = "ping " + host + " -w 1000 -n 1 > nul 2>&1"
    response = os.system(target)
    # Note:original response is 1 for fail; 0 for success; so we flip it
    return not response


def populatetargets(targetlist):
    """
    Simply opens a file and returns each line in a list
    """
    devicelist = []
    with open(targetlist, 'r') as f:
        for line in f:
            devicelist.append(line.strip())
    print('File parsed.')
    return devicelist


def checkmakedir(path):
    """
    Checks if the directory exists; creates it if absent
    """
    try:
        if not os.path.isdir(path):
            os.mkdir(path)
    except Exception as e:
        print(e)
        pass


def generateconfig(filename, args, folder='./cfg'):
    """
    Generate a template configuration file in the `./cfg` folder

    :param str filename: target destination file
    :param dict args: Sample configuration layout
    """
    if not os.path.isdir(folder):
        os.mkdir(folder)
    with open(folder + filename, 'w') as dc:
        json.dump(args, dc, indent=4, sort_keys=True)


def load_plugin(fullmodule):
    """
    Helper for dynamic importing of modules

    :param str fullmodule: Full module path in package, e.g.
                           `patheng.oauth2.OAuthAgent`
    :returns: module
    """
    try:
        package, module = fullmodule.rsplit('.', 1)
        modpack = import_module(package)
    except ValueError as e:
        if 'need more than 1' in str(e):
            return import_module(fullmodule)
    return getattr(modpack, module)


def allow_kwargs(func):
    """
    Decorator to match key-value pairs in a dictionary to positional and
    keyword arguments for a function.

    `Source to Stackoverflow <http://stackoverflow.com/a/11172483>`_

    .. code:: python
        # with your function:
        @allow_kwargs
        def foo(a = None, b=None, c=None):
          return "a:%s, b:%s, c:%s " % (a,b,c)

        # with someone_elses function:
        from some_place import foo
        foo = allow_kwargs(foo)

    :param func: Function to wrap
    """
    argspec = getargspec(func)
    # if the original allows kwargs then do nothing
    if argspec.keywords:
        return func

    @wraps(func)
    def newfunc(*args, **kwargs):
        # print "newfoo called with args=%r kwargs=%r"%(args,kwargs)
        some_args = dict((k, kwargs[k]) for k in argspec.args if k in kwargs)
        return func(*args, **some_args)
    return newfunc


def tofrom_utc(timestamp, parseformat, from_utc=True):
    """
    Convert a timestamp to/from UTC time

    :param str timestamp: Date/time to modify
    :param str parseformat: Format of the timestamp to parse
    :param bool from_utc: True if source stamp is UTC; otherwise False
    :return: Converted timestamp
    :rtype: str
    """
    utc_zone = tz.tzutc()
    local_zone = tz.tzlocal()

    time_obj = datetime.strptime(timestamp, parseformat)
    new_time = time_obj.replace(tzinfo=(local_zone, utc_zone)[from_utc])
    new_time = new_time.astimezone((utc_zone, local_zone)[from_utc])
    return new_time.strftime(parseformat)

if sys.version_info[0] == 2:
    def to_option43(options):
        '''
        Create a hex-encoded string for DHCP Option 43

        Key values should be the Sub-option numbers (int or str)

        :param dict options: Sub-options and values
        :return: Hex stream
        :rtype: str
        '''
        def to_hex(option, content):
            hexform = '{option}{length}{content}'
            return hexform.format(**{
                'option': hex(int(option))[2:].zfill(2).upper(),
                'length': hex(len(content))[2:].zfill(2).upper(),
                'content': str(hexlify(bytes(content))).upper()
            })
        return ''.join([to_hex(k, v) for k, v in options.iteritems()])

    def from_option43(hexstream):
        '''
        Decode a hex string for DHCP Option 43

        :param str hexstream: Hex-encoded option string

        :return: Options and their values
        :rtype: dict
        '''
        options = {}
        stream = hexstream
        while stream:
            option = int(stream[0:2], 16)
            length = int(stream[2:4], 16)
            content = unhexlify(bytes(stream[4:(length * 2) + 4]))
            stream = stream[(length * 2) + 4:]
            options[option] = content
        return options

else:
    def to_option43(options):
        '''
        Create a hex-encoded string for DHCP Option 43

        Key values should be the Sub-option numbers (int or str)

        :param dict options: Sub-options and values
        :return: Hex stream
        :rtype: str
        '''
        def to_hex(option, content):
            hexform = '{option}{length}{content}'
            return hexform.format(**{
                'option': hex(int(option))[2:].zfill(2).upper(),
                'length': hex(len(content))[2:].zfill(2).upper(),
                'content': str(
                    hexlify(bytes(content, 'utf-8')), 'utf-8').upper()
            })
        return ''.join([to_hex(k, v) for k, v in options.items()])

    def from_option43(hexstream):
        '''
        Decode a hex string for DHCP Option 43

        :param str hexstream: Hex-encoded option string

        :return: Options and their values
        :rtype: dict
        '''
        options = {}
        stream = hexstream
        while stream:
            option = int(stream[0:2], 16)
            length = int(stream[2:4], 16)
            content = str(
                unhexlify(bytes(stream[4:(length * 2) + 4], 'utf-8')), 'utf-8')
            stream = stream[(length * 2) + 4:]
            options[option] = content
        return options
