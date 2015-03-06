from string import upper, replace
import re

import utils
import S57names

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
        if self.mode != "SQL" and self.mode != "LOVE":
            utils.log("Warning, rule {}: Only SQL and LOVE modes are supported, unknown mode {}.".format(self.id, mode))
            return None
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
                if self.fcsubtype == -1:
                    utils.log("Error, rule {}: Invalid fc or fcsubtype, {}/{}.".format(self.id, fc, fcsubtype))
                    self.id = -1
                    return None
        # Condition
        self.condition = replace(condition, "!=", "<>")
        if ('"' in self.condition): # double quotes won't work
            if(not "'" in self.condition):
                self.condition = replace(self.condition, '"', "'")
                utils.log("Warning, rule {}: Can't have \"double quotes\" in condition, using 'single quotes' instead.".format(self.id))
            else:
                print "Error, rule {}: There are both \"double quotes\" and 'single quotes' in condition - this will fail.".format(self.id)
                utils.log("Error, rule {}: There are both \"double quotes\" and 'single quotes' in condition - this will fail.".format(self.id))
        if (self.mode == 'LOVE'):
            if (not '%' in self.condition):
                utils.log("Error, rule {}: LOVE rule without % character.".format(self.id))
                return None
            if (fixorlog == 'FIX'):
                utils.log("Warning, rule {}: LOVE rule with FIX. Treating as LOG.".format(self.id))
                fixorlog = 'LOG'
            self.condition = [val.strip() for val in condition.split('%')]
            self.condition[1] = [val.strip() for val in self.condition[1][1:-1].split(',') ]
        # Fix or Log - self.dofix is a bool
        self.dofix = (fixorlog=="FIX")
        self.fixLst = []
        # Fix value
        # - for FIXes, self.fixLst is a list of pairs of fixes, e.g. PLTS_COMP_SCALE=90000,IS_CONFLATE=TRUE
        # - for LOGs, self.fixLst is a list of field names to include in log output
        if self.dofix:
            if fixvalue: # there's probably a cleaner way of doing this looping and cleaning...
                # TODO: recognize a fixvalue which is another column name
                self.fixLst = [fixpair.split("=") for fixpair in fixvalue.split(",")] # split on , and =
                self.fixLst = [[val.strip() for val in fixpair] for fixpair in self.fixLst] # strip whitespace
                for fix in self.fixLst:
#                    fix = [val.strip() for val in fix] # strip whitespace
                    fix[1] = CleanUpFixString(fix[1]) # ugly quote mark removal, recognising None, NULL, UNKNOWN and typecasting int/float
                #print self.fixLst
            else:
                self.dofix = False
                utils.log("Warning, rule {}: FIX with no repair values; treating as LOG.".format(str(self.id)))
                # if the user didn't supply a fix value, this is more helpful than throwing an error
        elif fixvalue: # list of fields to report on
            self.fixLst = [val.strip() for val in fixvalue.split(',')] # split by comma and strip whitespace
        # compose Where String
        self.whereString = ''
        if self.fcsubtype != "*":
            fcs = "FCSubtype"
            if "," in self.fcsubtype:
                fcs = fcs + " IN (" + self.fcsubtype + ")"
            else:
                fcs = fcs + " = " + self.fcsubtype
            self.whereString = fcs + " AND " 
        if self.mode == 'LOVE':
            # get values that contain a comma, or are individual and invalid
            self.whereString += "(" + self.condition[0] + " NOT IN (" + ','.join(["'"+s+"'" for s in self.condition[1]]) + ", '-32767', NULL) OR " + self.condition[0] + " LIKE '%,%')"
            #self.fixLst.append(self.condition[0])
        else:
            self.whereString += "(" + self.condition + ")"
           
    def GetWhereString(self):
        """Return a string with the WHERE clause for the rule, includes: condition and fcsubtype."""
        return self.whereString
        #if self.mode == 'LOVE':
        #    return self.condition[0] + " NOT IN (" + ','.join(["'"+s+"'" for s in self.condition[1]]) + ", '-32767') OR " + self.condition[0] + " LIKE '%,%'"
        #    #return self.condition[0] + " LIKE '%,%'" # TODO: takes 14 secs, vs. 27 sec.
        #where = self.condition
        #if(self.fcsubtype != "*"):
        #    fcs = "FCSubtype"
        #    if "," in self.fcsubtype:
        #        fcs = fcs + " IN (" + self.fcsubtype + ")"
        #    else:
        #        fcs = fcs + " = " + self.fcsubtype
        #    where = fcs + " AND " + where
        #return where
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
    if utils.isFloat(fixvalue): # this will also match on int, so check that first
        return float(fixvalue.replace(",", ".", 1)) # accept either , or . as decimal separator
    return fixvalue

def ReadRules(path):
    """Read rules from a file, and return a list of Rule objects"""
    lst_rules = list()
    try:
        with open(path, 'r') as f:
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
                if len(items)!=10: # SQL and LOVE rules both have 10 elements
                    utils.log("Warning: Line does not contain the correct number of elements. Ignoring this rule. \n\t"+line.strip()+"\n\t"+repr(items))
                    continue
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
            print "Done reading rules."
    except IOError, e:
        utils.log(e.errno)
        utils.log(e)
        return 101
    return lst_rules
