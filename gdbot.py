"""
    GDBOT - a Geodatabase (ro)bot
    The purpose of this project is to keep a geo data base clean and tidy
    The script acts based on a number of rules, the rules are stores in a .gdbot file
    
    Author: Martin Hvidberg <mahvi@gst.dk>
    Author: Hanne L. Petersen <halpe@gst.dk>
    
    Ver. 0.2
    
    To do:
    
        - Work with NIS, not just with .gdb
        
        - Figure out why we can't have double quotes in condition input. Fix it, convert them, or detect and issue a warning
        
"""

import arcpy
import os, re
from string import upper, replace
from datetime import datetime # for datetime.now()
import S57names

lst_log = [] # Collector list for things to log ...
logfilename = ""

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

floatPattern = re.compile("^[0-9.,]+$")
def isfloat(string):
    """ Check if string looks like a float (or int) number. """
    return re.search(floatPattern, string)

def log(string):
    """Append message to the log"""
    global lst_log
    print string
    #lst_log.append(string) # TODO: either do this or write to file
    with open(logfilename, 'a') as thefile:
        thefile.write("%s\n" % string)
    return 0

def writeLogToFile(filename):
    """Write compiled log messages to file"""
    with open(filename, 'w') as thefile:
        for logline in lst_log:
            thefile.write("%s\n" % logline)

class Rule:
    def __init__(self, theid, title, mode, fc, fcsubtype, condition, fixorlog, fixvalue):
        # The ID
        self.id = theid
        # Title
        self.title = title
        # Mode
        self.mode = upper(mode)
        if self.mode != "SQL":
            log("Warning, rule {}: Only SQL mode is supported, unknown mode {}.".format(self.id, mode))
        # FC - self.fclist is a list, possibly with only one element
        if(fc=="*"):
            self.fclist = lstNISlayers
            if(fcsubtype != "*"):
                log("Warning, rule {}: Feature class is *, but feature class subtype is {}.".format(self.id, fcsubtype))
        else:
            self.fclist = fc.split(",") # split will return a list, even if there are no commas
        # FCsubtype - self.fcsubtype is a comma-separated string, NOT a list
        fcsubtype = fcsubtype.strip()
        if fcsubtype == "*" or fcsubtype == "":
            self.fcsubtype = "*"
        elif(re.search("[A-Za-z]", fcsubtype) and len(self.fclist)>1): # can't handle s57-fcs with multiple fc
            log("Error, rule {}: Can't handle fc subtype abbreviations ({}) for multiple feature classes ({}).".format(self.id, fcsubtype, fc))
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
                print self.fixLst
            else:
                self.dofix = False
                log("Warning, rule {}: FIX with no repair values; treating as LOG.".format(str(self.id)))
                 # if the user didn't supply a fix value, this is more helpful than throwing an error
        elif fixvalue:
                log("Warning, rule {}: FIX is not set, but repair value is non-empty.".format(str(self.id)))
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
        log("Warning: Can't interpret fcsubtype: {}.".format(fcsubtype))
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
    if isfloat(fixvalue): # this will also match on int, so check that first
        return float(fixvalue.replace(",", ".", 1)) # accept either , or . as decimal separator
    return fixvalue


def ConnectToDB(db):
    arcpy.env.workspace = db
    desDB = arcpy.Describe(db)
    if desDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":
        print "it's an SDE geodatabase"
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
        print "it's a File geodatabase"
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.AccessWorkspaceFactory.1":
        # it's a Personal geodatabase
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.InMemoryWorkspaceFactory.1":
        # it's an in_memory workspace
        pass
    elif desDB.workspaceFactoryProgID == "":
        # it's an Other (shapefile, coverage, CAD, VPF, and so on)
        pass
    else: # It's not a recognizable DB
        pass
    
    return "the connection in some form...Where it's clear if it is versioned"

def ReadRules(path):
    """Read rules from a file, and return a list of Rule objects"""
    lst_rules = list()
    f = open(path, 'r')
    for line in f:
        if(not line.strip() or line[0]=="#"):
            continue
        if(line[0]=="%"):
            log("ignoring % lines, not implemented yet")
            continue
        if(line[0]!=":"):
            log("Warning: ignoring invalid line starting with "+line[0]+" ("+line+")")
            continue
        if("#" in line):
            line = line.split("#")[0].strip()
        items = line.split(":") 
        if len(items)!=10:
           log("Warning: Line does not contain the correct number of elements... \n\t"+line.strip()+"\n\t"+repr(items))
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

def CheckTables(dataset, rules):
    """Check the tables of the given dataset, according to the rules"""
    # If you get: "RuntimeError: An expected Field was not found or could not be retrieved properly."
    # don't use double quotes in condition input, use single quotes!!!
    for rule in rules:
        if(rule.dofix): # FIX
            # v. 0.1: print "UPDATE " + str(rule.fclist) + " SET " + rule.field + " = " + rule.fixvalue + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["OBJECTID", "LNAM"] # fields to get from the db, update log writing below if this changes
                defaultFieldsNum = len(fields)
                for correction in rule.fixLst: # add the columns that we're going to fix
                    fields.append(correction[0])
                with arcpy.da.UpdateCursor(dataset+"Nautical/"+fc, fields, where_clause=rule.GetWhereString()) as uc:
                    for row in uc:
                        count += 1
                        logStr = "Rule {} ({}): updating " .format(rule.id, rule.title)
                        i = defaultFieldsNum
                        for i in range(len(rule.fixLst)): # do each of the fixes
                            logStr += "{} = {} (was {}), ".format(rule.fixLst[i][0], rule.fixLst[i][1], row[defaultFieldsNum+i])
                            fixVal = rule.fixLst[i][1] # set the update value
                            row[defaultFieldsNum+i] = fixVal
                            i += 1
                        logStr = logStr[0:-2] + " for OBJECTID = {} in {}".format(row[0], fc)
                        log(logStr)
                        uc.updateRow(row) # do the actual update
                        pass
                log("Total {} fix hits for rule {}".format(count, rule.id))
        else: # LOG
            # v. 0.1: print "SELECT FROM " + str(rule.fclist) + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["OBJECTID", "LNAM"] # fields to get from the db, update log writing below if this changes
                with arcpy.da.SearchCursor(dataset+"Nautical/"+fc, fields, where_clause=rule.GetWhereString()) as sc:
                    for row in sc:
                        count += 1
                        log("Found rule {} ({}) violation for OBJECTID={} in {}"
                            .format(rule.id, rule.title, row[0], fc))
                        # TODO: Nice to have: include the current value of the field(s) - can we parse the requested field names out of the condition string
                log("Total {} search hits for rule {}".format(count, rule.id))
    log("Done checking tables.")

def RunGdbTests():
    """Test on a file gdb to verify syntax and rule validity."""
    global logfilename
    logfilename = "test.log"
    readrules  = "./readtest.gdbot"
    checkrules = "./ruletest.gdbot"
    log("*** Start GDBtest. "+str(datetime.now())+" ***")
    
    print "Starting read tests..."
    lst_rules = ReadRules(readrules)
    #print lst_rules
    for rule in lst_rules:
        print " Rule: "+rule.__repr__().strip()
    print "Finished read tests."
    return
    
    lst_rules = []
    
    print "Starting check tests..."
    #dataset = "./clip_67_67_5_til_1411.gdb/"
    #dataset = "./1462hAndheld.gdb/"
    datazip = "../test.gdb.zip"
    dataset = ".\\"+datazip[3:-4]+"\\"
    try:
        print "deleting test gdb..."
#         os.system("del /q %s" % (dataset))
        print "extracting test gdb..."
#         os.system("unzip -q %s" % (datazip))
        # unzipping will produce an error:
        # test.gdb/:  ucsize 163840 <> csize 0 for STORED entry ; continuing with "compressed" size value
        # but seems to work fine anyway
        pass
    except BaseException as e:
        print "system command (delete/extract/...) failed: " + str(e)
    lst_rules = ReadRules(checkrules)
    print lst_rules
    CheckTables(dataset, lst_rules)
    print "Finished check tests."
    
    # TODO: compare the log file output to the expected output
    # 'C:\Program Files (x86)\WinMerge\WinMergeU.exe' ...
    # TODO: compare the resulting gdb to the expected result
    #writeLogToFile('log.txt')


def main(db, rulefile, logfile):
    
    # Read the .gdbot file and build the list of bot-rules
    lstRules = ReadRules(rulefile)
    
    # Make connection to a db
    conDB = ConnectToDB(db)
    
    # Create a version, if applicable, and change to it
    try:
        dbVersion = arcpy.CreateVersion_management (conDB,"NIS.DEFAULT","kill999","PROTECTED")
        print "Check...", dbVersion
    except arcpy.ExecuteError as e:
        print repr(e)#"I/O error({0}): {1}".format(e.errno, e.strerror)
    
    # Start an edit session
    
    # *** Walk the db, and use the rules on it - This is the big enchilada
    CheckTables(conDB, lstRules)
    
    # Reconcile and Post the version, if allowed by the run mode
    # arcpy.ReconcileVersions_management
    
    # Stop the edit session
    
    # Remove the Version if Posted
    
    # Disconnect from db
    
    # Finish off logfiles, etc. and clean up nicely...
    
    
    return 0
    
if __name__ == "__main__":
    RunGdbTests()
    db = "M:\HAL\TeamNIS\Tools\SDE_connections\Yellow_Test\yellow_nis@NIS_EDITOR.sde"
    #db = "M:\HAL\TeamNIS\Tools\SDE_connections\green2_nis@nis_editor.sde"
    #db = "Database Connections\green2_nis@nis_editor.sde"
    #db = "C:\Martin\Work_Eclipse\BuildGreen\data\input.gdb"
    db = "./input.gdb"
    #main(db, rules, "log.txt")

else:
    print "Non-recognized caller: "+__name__
