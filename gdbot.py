"""
    GBOT - a Geodatabase (ro)bot
    The purpose of this project is to keep a geo data base clean and tidy
    The script act based on a number of rules, the rules are stores in a .gbot file
    
    Author : Martin Hvidberg <mahvi@gst.dk>
    Author : Hanne L. Petersen <halpe@gst.dk>

    To do:
    
        Look for XXX in the code 
        
        Allow the rule reader to understand S-57 codes, e.g. PortsAndServicesP FCsubtype 15 is actually called CRANES
            : 3 : Cranes can no longer be CATCRN = 1. Change to unknown : PortsAndServicesP : 15 : CATCRN = 1 : : FIX : -32767 :
            : 3 : Cranes can no longer be CATCRN = 1. Change to unknown : PortsAndServicesP : CRANES : CATCRN = 1 : : FIX : -32767 :
    
"""

import arcpy
#import os
from string import upper, replace

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
    def __init__(self, theid, title, fc, fcsubtype, mainfield, errval, othercond, fixorlog, fixvalue):
        self.id = theid
        self.title = title
        if(fc=="*"):
            self.fclist = lstNISlayers
            if(fcsubtype != "*"):
                log("Warning, rule {}: Feature class is *, but feature class subtype is {}.".format(self.id, fcsubtype))
        else:
            self.fclist = ConvertToList(fc)
        self.fcsubtype = fcsubtype
        if(not self.fcsubtype):
            self.fcsubtype = "*"
        self.field = mainfield
        self.errval = replace(errval, "!=", "<>")
        if(self.errval[0] != "=" and upper(self.errval[0:2]) != "IS" and self.errval[0:2] != "<>"):
            log("Warning, rule {}: no = or IS operator in error condition: {} ?".format(str(self.id), errval[0:2]))
        self.othercond = replace(othercond, "!=", "<>")
        self.dofix = (fixorlog=="FIX")
        #=======================================================================
        # # This is ugly: we're stripping quote marks off fix value, even though it's a string.
        # # They're required in the test value, but not allowed in the fix value,
        # # so we'll allow the user to enter them in both places, and remove them here.
        # if(fixvalue and fixvalue[0] == fixvalue[-1] and (fixvalue[0]=="'" or fixvalue[0]=='"')):
        #     fixvalue = fixvalue[1:-1]
        # self.fixvalue = fixvalue
        self.fixvalue = fixvalue.strip("\"\'") # This is shorter
        #=======================================================================
        
        # TODO: recognize a fixvalue which is another column name
        if(self.dofix and not self.fixvalue):
            self.dofix = 0 # <- Should this be False? XXX
            log("Warning, rule {}: ignoring FIX with no repair value.".format(str(self.id)))
             # This is an Error (not a Warning). The rule should not be added to the rule set... XXX
        if(self.fixvalue and not self.dofix):
            log("Warning, rule {}: FIX is not set, but repair value is non-empty.".format(str(self.id)))
    def GetWhereString(self):
        """Return a string with the WHERE clause for the rule, includes: field, errvalue, fcsubtype, and othercond."""
        where = self.field + ' ' + self.errval
        if(self.fcsubtype != "*"):
            where = where + " AND FCSubtype"
            if "," in self.fcsubtype:
                where = where + " IN (" + self.fcsubtype + ")"
            else:
                where = where + " = " + self.fcsubtype
        if(self.othercond):
            where = where + " AND " + self.othercond
        return where
    def __repr__(self):
        fixstring = ""
        if(self.dofix):
            fixstring = "{} = {}".format(str(self.field), str(self.fixvalue))
        return "({}, {}, {}, ({}), \"{}\", {}:\"{}\")\n".format(\
        str(self.id), str(self.title), str(self.fclist), str(self.fcsubtype),
            self.GetWhereString(), str(self.dofix), fixstring)
# end class Rule

def ConvertToList(string, delimiter=","):
    """Convert a string to a list"""
    #=========================================================================== This is not necessary, .split() will handle that just fin 
    # if(not delimiter in string):
    #     return [string]
    #===========================================================================
    return string.split(delimiter)

def ConnectToDB(db):
    # TODO
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
        line = line.strip() # Stripping lead and trailing whitespaces
        if(not line.strip() or line[0]=="#"):
            continue
        if(line[0]=="%"):
            log("ignoring % lines")
            continue
        if(line[0]!=":"):
            log("Warning: ignoring invalid line starting with "+line[0])
            continue
        if("#" in line):
            #log("Warning: not handling mid-line #'s") # TODO
            line = line.split("#")[0].strip()
        items = line.split(":") 
        if len(items)!=11:
           log("Warning: Line do not contain the correct number of elements... \n\t"+line.strip()+"\n\t"+repr(items))
        # forget about number 0, since its always an empty string (nothing in front of the first ':'
        ruleid = items[1].strip()
        title = items[2].strip()
        featureclass = items[3].strip()
        fcsubtype = items[4].strip()
        field = items[5].strip()
        errorvalue = items[6].strip()
        sec_cond = items[7].strip()
        fixorlog = items[8].strip()
        fixvalue = items[9].strip()
        r = Rule(ruleid, title, featureclass, fcsubtype, field, errorvalue, sec_cond, fixorlog, fixvalue)
        lst_rules.append(r)
    f.close()
    print "Done reading rules."
    return lst_rules

def CheckTables(dataset, rules):
    """Check the tables of the given dataset, according to the rules"""
    for rule in rules:
        if(rule.dofix): # FIX
            #print "UPDATE " + str(rule.fclist) + " SET " + rule.field + " = " + rule.fixvalue + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["PLTS_COMP_SCALE", "LNAM", rule.field] # watch the numbering, update below!
                # TODO: if fixvalue is column name, do we need to include it here?
                with arcpy.da.UpdateCursor(dataset+"Nautical/"+fc, fields, rule.GetWhereString()) as uc:
                    for row in uc:
                        count += 1
                        log("Rule {} ({}): updating {} = {} (was {}) for LNAM={}"
                            .format(rule.id, rule.title, rule.field, rule.fixvalue, row[2], row[1]))
                        row[2] = rule.fixvalue
                        uc.updateRow(row)
                        pass
                log("Total {} update hits for rule {}".format(count, rule.id))
        else: # LOG
            #print "SELECT FROM " + str(rule.fclist) + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["PLTS_COMP_SCALE", "LNAM", rule.field]
                with arcpy.da.SearchCursor(dataset+"Nautical/"+fc, fields, where_clause=rule.GetWhereString()) as sc:
                    for row in sc:
                        count += 1
                        log("Found rule {} ({}) violation with {}={} for LNAM={} in {}"
                            .format(rule.id, rule.title, rule.field, row[2], row[1], fc))
                log("Total {} search hits for rule {}".format(count, rule.id))
    log("Done checking tables.")

def RunGdbTests():
    """Test on a file gdb to verify syntax and rule validity."""
    global logfilename
    logfilename = "test.log"
    readrules  = "./readtest.gdbot"
    checkrules = "./ruletest.gdbot"
    log("")
    
    print "Starting read tests..."
    lst_rules = ReadRules(readrules)
    #print lst_rules
    for rule in lst_rules:
        print " Rule: "+rule.__repr__().strip()
    print "Finished read tests."
    
    lst_rules = []
    
    print "Starting check tests..."
    dataset = "./clip_67_67_5_til_1411.gdb/"
    #dataset = "./1462hAndheld.gdb/"
    dataset_copy = "./testdata.gdb/"
    try:
        #print "deleting..."
        #arcpy.Delete_management(dataset_copy)
        #os.system("del /q %s" % (dataset_copy))
        #print "copying:"
        #arcpy.Copy_management(dataset, dataset_copy)
        #os.system("xcopy /s %s %s" % (dataset, dataset_copy))
        pass
    except ExecuteError as e:
        print "deleting failed: " + str(e)
    lst_rules = ReadRules(checkrules)
    print lst_rules
    CheckTables(dataset_copy, lst_rules)
    print "Finished check tests."
    
    # TODO: compare the log file output to the expected output
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
        print "Check...",dbVersion
    except arcpy.ExecuteError as e:
        print repr(e)#"I/O error({0}): {1}".format(e.errno, e.strerror)
    
    # Start an edit session
    
    # *** Walk the db, and use the rules on it - This is the big enchilada
    CheckTables(conDB, lstRules)
    
    # Reconcile and Post the version, if allowed by the run mode
    
    # Stop the edit session
    
    # Remove the Version if Posted
    
    # Disconnect from db
    
    # Finish off logfiles, etc. and clean up nicely...
    
    
    return 0
    
if __name__ == "__main__":
    RunGdbTests()
    #db = "Database Connections\green2_nis@nis_editor.sde"
    #db = "C:\Martin\Work_Eclipse\BuildGreen\data\input.gdb"
    db = "./input.gdb"
    #main(db, rules, "log.txt")

else:
    print "Non recognized caller: "+__name__
