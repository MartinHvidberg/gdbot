import re

lst_log = [] # Collector list for things to log ...


def log(string):
    """Append message to the log."""
    global lst_log
    #print string
    lst_log.append(string) # TODO: either do this or write to file
#     with open(logfilename, 'a') as thefile:
#         thefile.write("%s\n" % string)
    return 0

def writeLogToFile(filename):
    """Write compiled log messages to file."""
    with open(filename, 'w') as thefile:
        for logline in lst_log:
            thefile.write("%s\n" % logline)

floatPattern = re.compile("^[0-9.,]+$")
def isfloat(string):
    """ Check if string looks like a float (or int) number. """
    return re.search(floatPattern, string)

def encodeIfUnicode(strval):
    """Encode if string is unicode."""
    if isinstance(strval, unicode):
        return strval.encode('utf8')
    return str(strval)

