import arcpy

import utils

def SetUpDB(db):
    """Connect to database with .sde connection, and prepare a version for editing."""

    # Create a version and change to it
    try:
        dbVersion = arcpy.CreateVersion_management (db, "NIS.DEFAULT", "kill999", "PROTECTED")
        print "Check...", dbVersion
    except arcpy.ExecuteError as e:
        print "Failed to create version:"
        print repr(e)#"I/O error({0}): {1}".format(e.errno, e.strerror)
        return False
    
    # Start an edit session
    
    return True #"the connection in some form...Where it's clear if it is versioned"


def FinishUpDB(db):
    """Reconcile and Post the version, and clean up."""
    
    # Reconcile and Post the version, if allowed by the run mode
    # arcpy.ReconcileVersions_management
    
    # Stop the edit session
    
    # Remove the version if posted
    # arcpy.DeleteVersion_management(db, newName)
    
    # Disconnect from db
    
    return


def CheckData(dataset, rules):
    """Check a dataset, given by either .sde or .gdb, using the given rule set."""
    
    sdeMode = False
    desDB = arcpy.Describe(dataset)
    if desDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":
        sdeMode = True
        print "It's an SDE geodatabase"
        pass
    elif desDB.workspaceFactoryProgID != "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
        print "Unexpected data format. Should be .sde or .gdb."
        return
    
    if sdeMode:
        if not SetUpDB(dataset):
            print "Problem connecting to database, quitting"
            return
    
    # *** Walk the db, and use the rules on it - This is the big enchilada
    CheckTables(dataset, rules)
    
    if sdeMode:
        FinishUpDB(dataset) # Finish and cleanup: Reconcile, Post, delete version
    

def CheckTables(dataset, rules):
    """Check the tables of the given dataset, according to the rules.
    
    The dataset is either a .gdb file, or a connection to an sde ready to be used."""
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
                        utils.log(logStr)
                        uc.updateRow(row) # do the actual update
                        pass
                utils.log("Total {} fix hits for rule {}".format(count, rule.id))
        else: # LOG
            # v. 0.1: print "SELECT FROM " + str(rule.fclist) + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["OBJECTID", "LNAM"] # fields to get from the db, update log writing below if this changes
                with arcpy.da.SearchCursor(dataset+"Nautical/"+fc, fields, where_clause=rule.GetWhereString()) as sc:
                    for row in sc:
                        count += 1
                        utils.log("Found rule {} ({}) violation for OBJECTID={} in {}"
                            .format(rule.id, rule.title, row[0], fc))
                        # TODO: Nice to have: include the current value of the field(s) - can we parse the requested field names out of the condition string
                utils.log("Total {} search hits for rule {}".format(count, rule.id))
    utils.log("Done checking tables.")

