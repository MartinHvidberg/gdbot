from string import upper, replace
import re

import utils
import S57names

lst_log = [] # Collector list for things to log ...

## Defining all the layer names that are to be found in a NIS
lstNISlayers = ['AidsToNavigationP', 
                'CoastlineA', 'CoastlineL', 'CoastlineP', 
                'CulturalFeaturesA', 'CulturalFeaturesL', 'CulturalFeaturesP', 
                'DangersA', 'DangersL', 'DangersP', 
                'DepthsA', 'DepthsL', 
                'IceFeaturesA', 
                'MetaDataA', 'MetaDataL', 'MetaDataP', 
                'MilitaryFeaturesA', 'MilitaryFeaturesP', 
                'NaturalFeaturesA', 'NaturalFeaturesL', 'NaturalFeaturesP', 
                'OffshoreInstallationsA', 'OffshoreInstallationsL', 'OffshoreInstallationsP', 
                'PortsAndServicesA', 'PortsAndServicesL', 'PortsAndServicesP', 
                'RegulatedAreasAndLimitsA', 'RegulatedAreasAndLimitsL', 'RegulatedAreasAndLimitsP', 
                'SeabedA', 'SeabedL', 'SeabedP', 
                'SoundingsP', 
                'TidesAndVariationsA', 'TidesAndVariationsL', 'TidesAndVariationsP', 
                'TracksAndRoutesA', 'TracksAndRoutesL', 'TracksAndRoutesP', 
                'UserDefinedFeaturesA', 'UserDefinedFeaturesL', 'UserDefinedFeaturesP']

class Rule:
    def __init__(self, theid, title, mode, fc, fcsubtype, condition, fixorlog, fixvalue):
        # The ID
        self.id = theid
        # Title
        self.title = title
        # Mode
        self.mode = upper(mode)
        if self.mode != "SQL":
            utils.log("Warning, rule {}: Only SQL mode is supported, unknown mode {}.".format(self.id, mode))
        # FC - self.fclist is a list, possibly with only one element
        if(fc=="*"):
            self.fclist = lstNISlayers
            if(fcsubtype != "*"):
                utils.log("Warning, rule {}: Feature class is *, but feature class subtype is {}.".format(self.id, fcsubtype))
        else:
            self.fclist = fc.split(",") # split will return a list, even if there are no commas
        # FCsubtype - self.fcsubtype is a comma-separated string, NOT a list
        fcsubtype = fcsubtype.strip()
        if fcsubtype == "*" or fcsubtype == "":
            self.fcsubtype = "*"
        elif(re.search("[A-Za-z]", fcsubtype) and len(self.fclist)>1): # can't handle s57-fcs with multiple fc
            utils.log("Error, rule {}: Can't handle fc subtype abbreviations ({}) for multiple feature classes ({}).".format(self.id, fcsubtype, fc))
            self.id = -1
            return None
        else:
            if("," in fcsubtype):
                # split the list by comma, convert each to int if needed, and glue with commas again
                self.fcsubtype = ",".join([GetFCSids(fcs, self.fclist[0]) for fcs in fcsubtype.split(",")])
            else:
                self.fcsubtype = GetFCSids(fcsubtype, self.fclist[0])
        # Condition
        self.condition = replace(condition, "!=", "<>")
        # Fix or Log - self.dofix is a bool
        self.dofix = (fixorlog=="FIX")
        self.fixLst = []
        # Fix value (new value for main field) - self.fixLst is a list of pairs (lists)
        if self.dofix:
            if fixvalue: # there's probably a cleaner way of doing this looping and cleaning...
                # TODO: recognize a fixvalue which is another column name
                self.fixLst = [fixpair.split("=") for fixpair in fixvalue.split(",")] # split on , and =
                self.fixLst = [[val.strip() for val in fixpair] for fixpair in self.fixLst] # strip whitespace
                for fix in self.fixLst:
#                     fix = [val.strip() for val in fix] # strip whitespace
                    fix[1] = CleanUpFixString(fix[1]) # ugly quote mark removal, recognising None, NULL, UNKNOWN and typecasting int/float
                #print self.fixLst
            else:
                self.dofix = False
                utils.log("Warning, rule {}: FIX with no repair values; treating as LOG.".format(str(self.id)))
                 # if the user didn't supply a fix value, this is more helpful than throwing an error
        elif fixvalue:
                utils.log("Warning, rule {}: FIX is not set, but repair value is non-empty.".format(str(self.id)))
    def GetWhereString(self):
        """Return a string with the WHERE clause for the rule, includes: condition and fcsubtype."""
        where = self.condition
        if(self.fcsubtype != "*"):
            where = where + " AND FCSubtype"
            if "," in self.fcsubtype:
                where = where + " IN (" + self.fcsubtype + ")"
            else:
                where = where + " = " + self.fcsubtype
        return where
    def __repr__(self):
        return "({}; {}; {}; {}; \"{}\"; {}:{})\n".format(\
        str(self.id), str(self.title), str(self.fclist), str(self.fcsubtype),
            self.GetWhereString(), str(self.dofix), str(self.fixLst))
# end class Rule

def GetFCSids(fcsubtype, fc):
    """Return the number (as string) for the fc subtype."""
    fcsubtype = fcsubtype.strip()
    if fcsubtype.isdigit():
        return fcsubtype
    else: # If it's not an integer, it may be an S-57 '6-letter-code'
        fcs_value = S57names.S57ABBFC2FCSNumber(fcsubtype, fc)
        if fcs_value > 0:
            return fcs_value
        fcs_value = S57names.S57ABBFC2FCSNumber(fcsubtype, upper(fc)) # if we didn't find it, convert to uppercase and try again
        if fcs_value > 0:
            return fcs_value
        utils.log("Warning: Can't interpret fcsubtype: {}.".format(fcsubtype))
        return -1

def CleanUpFixString(fixvalue):
    """ If string starts and ends with matching quote marks, remove these; also convert None, NULL (and UNKNOWN), and convert to int/double. """
    # This is ugly: we're stripping quote marks off the fixvalue, even when it's a string.
    # They're required in the test value, but not allowed in the fix value,
    # so we'll allow the user to enter them in both places, and remove them here.
    if(fixvalue and fixvalue[0] == fixvalue[-1] and (fixvalue[0]=="'" or fixvalue[0]=='"')):
        fixvalue = fixvalue[1:-1]
    #if fixvalue.upper() == "UNKNOWN":
    #    return -32767 # TODO: is this a good idea? other values to accept?
    if fixvalue.upper() == "NULL" or fixvalue.upper() == "NONE":
        return None # make sure to return, the following lines will choke on a None
    if fixvalue.isdigit():
        return int(fixvalue)
    if utils.isfloat(fixvalue): # this will also match on int, so check that first
        return float(fixvalue.replace(",", ".", 1)) # accept either , or . as decimal separator
    return fixvalue

def ReadRules(path):
    """Read rules from a file, and return a list of Rule objects"""
    lst_rules = list()
    try:
        f = open(path, 'r')
    except IOError, e:
        print e.errno
        print e 
        return 101
    for line in f:
        if(not line.strip() or line[0]=="#"):
            continue
        if(line[0]=="%"):
            utils.log("ignoring % lines, not implemented yet")
            continue
        if(line[0]!=":"):
            utils.log("Warning: ignoring invalid line starting with "+line[0]+" ("+line+")")
            continue
        if("#" in line):
            line = line.split("#")[0].strip()
        items = line.split(":") 
        if len(items)!=10:
           utils.log("Warning: Line does not contain the correct number of elements... \n\t"+line.strip()+"\n\t"+repr(items))
        # forget about number 0, since it's always an empty string (nothing in front of the first ':')
        # number 9 is just comments
        ruleid = items[1].strip()
        title = items[2].strip()
        mode = items[3].strip()
        featureclass = items[4].strip()
        fcsubtype = items[5].strip()
        condition = items[6].strip()
        fixorlog = items[7].strip()
        fixvalue = items[8].strip()
        r = Rule(ruleid, title, mode, featureclass, fcsubtype, condition, fixorlog, fixvalue)
        if r.id != -1:
            lst_rules.append(r)
    f.close()
    print "Done reading rules."
    return lst_rules
