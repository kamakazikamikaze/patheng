import json
import os


def pinghost(host):
    """
    Ping target with a 1-second timeout limit

    Returns:
    response -- True if reached, otherwise False
    """
    host = host.split(':')[0]  # leave off the port if exists
    # print "Pinging"
    if os.name == 'posix':
        To_Ping = "ping -W1 -c 1 " + host + " > /dev/null 2>&1 "
    else:
        To_Ping = "ping " + host + " -w 1000 -n 1 > nul 2>&1"
    response = os.system(To_Ping)
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

    Keyword arguments:
    filename -- target destination file
    args -- a JSON of the sample configuration layout
    """
    if not os.path.isdir(folder):
        os.mkdir(folder)
    with open(folder + filename, 'w') as dc:
        json.dump(args, dc, indent=4, sort_keys=True)
