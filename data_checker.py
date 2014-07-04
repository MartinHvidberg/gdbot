import arcpy
import os

import utils

def SetUpDB(db):
    """Connect to database with .sde connection, and prepare a version for editing."""

    print "   < SetUpDB() >"
    arcpy.env.workspace = db # does this do anything?
    
    # Determine connection type - connType = 0 for .gdb, 1 for .sde
    connType = 0
    descDB = arcpy.Describe(db)
    if descDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":
        connType = 1
        print "It's an SDE geodatabase"
        pass
    elif descDB.workspaceFactoryProgID != "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
        print "Unexpected data format. Should be .sde or .gdb."
        return
    
    # Create a version and change to it
    # TODO?
#     try:
#         #dbVersion = arcpy.CreateVersion_management (db, "NIS.DEFAULT", "kill999", "PROTECTED")
#         print "Check..."#, dbVersion
#     except arcpy.ExecuteError as e:
#         print "Failed to create version:"
#         print repr(e)#"I/O error({0}): {1}".format(e.errno, e.strerror)
#         return False
#    arcpy.ChangeVersion_management("Nautical/CulturalFeaturesL", "TRANSACTIONAL", ""
    
    # we don't need Editor, startEditing and startOperation for file .gdbs
    if connType == 1:
        # Start an edit session. Must provide the workspace.
        #  http://resources.arcgis.com/en/help/main/10.2/index.html#//018w00000005000000
        edit = arcpy.da.Editor(db)
        
        # Edit session is started without an undo/redo stack for versioned data
        #  (for second argument, use False for unversioned data)
        edit.startEditing(False, True)
        
        # Start an edit operation
        edit.startOperation()
        
    else:
        edit = None
    
    # Create the db string with the name, depending on the database type.
    #  The final format we need to generate from this is something like
    #  file.gdb/Nautical/CulturalFeaturesL OR nis_editor@yellow.sde/NIS.Nautical/NIS.CulturalFeaturesL
    if connType == 1:
        db += "/NIS.Nautical/NIS."
    else:
        db += "/Nautical/"
    print "sde db = {}".format(db)
    
    return [db, edit]


def FinishUpDB(db, edit):
    """Reconcile and Post the version, and clean up."""
    
    print "   < FinishUpDB() >"
    # Reconcile and Post the version, if allowed by the run mode
    # TODO?
    # arcpy.ReconcileVersions_management
    
    # Stop the edit operation
    edit.stopOperation()
    
    # Stop the edit session and save the changes
    edit.stopEditing(True)
   
    # Remove the version if posted
    # TODO?
    # arcpy.DeleteVersion_management(db, newName)
    
    # Disconnect from db
    # TODO???
    
    return 0


def CheckData(dataset, rules):
    """Check a dataset, given by either .sde or .gdb, using the given rule set."""
    # dataset is something like "Database Connections/yellow_nis@NIS_EDITOR.sde" or "file.gdb"
    # db_str is something like "Database Connections/yellow_nis@NIS_EDITOR.sde/NIS.Nautical/NIS."
    # or "file.gdb/Nautical/" - which can be suffixed with a fc name like "CulturalFeaturesA"

    print "   < CheckData() >"
    
    # Set up database connection and edit session
    try:
        db_str, db_editSess = SetUpDB(dataset)
    except:
        print "Problem connecting to database, quitting"
        return 102
    
    # *** Walk the db, and use the rules on it - This is the big enchilada
    CheckTables(db_str, rules)
    
    # Finish and cleanup the edit session - only really needed for sde
    if "@" in db_str:
        FinishUpDB(dataset, db_editSess)
    

def CheckTables(dataset, rules):
    """Check the tables of the given dataset, according to the rules.
    
    The dataset is either a .gdb file, or a connection to an sde ready to be used."""
    
    # If you get: "RuntimeError: An expected Field was not found or could not be retrieved properly."
    # don't use double quotes in condition input, use single quotes!!!

    print "   < CheckTables() >"
    
    for rule in rules:
        if(rule.dofix): # FIX
            # v. 0.1: 
            print "UPDATE " + str(rule.fclist) + " SET " + rule.field + " = " + rule.fixvalue + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["OBJECTID", "LNAM"] # fields to get from the db, update log writing below if this changes
                defaultFieldsNum = len(fields)
                for correction in rule.fixLst: # add the columns that we're going to fix
                    fields.append(correction[0])
                with arcpy.da.UpdateCursor(dataset+fc, fields, where_clause=rule.GetWhereString()) as uc:
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
                with arcpy.da.SearchCursor(dataset+fc, fields, where_clause=rule.GetWhereString()) as sc:
                    for row in sc:
                        count += 1
                        utils.log("Found rule {} ({}) violation for OBJECTID={} in {}"
                            .format(rule.id, rule.title, row[0], fc))
                        # TODO: Nice to have: include the current value of the field(s) - can we parse the requested field names out of the condition string
                utils.log("Total {} search hits for rule {}".format(count, rule.id))
    utils.log("Done checking tables.")

