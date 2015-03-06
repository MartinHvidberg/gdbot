import arcpy
import os

import utils
import S57names

TEST_RULES_ONLY = True

def SetUpDB(db, withEditSess):
    """Connect to database with .sde connection, and prepare a version for editing."""

    utils.log("   < SetUpDB() >")
    arcpy.env.workspace = db # does this do anything?
    utils.log("   "+db)
    
    # Determine connection type - connType = 0 for .gdb, 1 for .sde
    connType = 0
    descDB = arcpy.Describe(db)
    
    if descDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory.1" or descDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory":
        connType = 1
        utils.log("     It's an SDE geodatabase")
        pass
    elif descDB.workspaceFactoryProgID != "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
        utils.log("Unexpected data format. Should be .sde or .gdb, was {}".format(descDB.workspaceFactoryProgID))
        return
    #connType = arcpy_utils.GetConnectionType(descDB)
    #if connType == -1:
    #    utils.log("Unexpected data format. Should be .sde or .gdb, was {}".format(descDB.workspaceFactoryProgID))
    #    return
        
    
    # We don't need to use an edit version, changes will still be recognised when the products do Get Changes.
    # NIS_MODIFIED etc. will be left unchanged
    # Create a version and change to it
#     try:
#         #dbVersion = arcpy.CreateVersion_management (db, "NIS.DEFAULT", "kill999", "PROTECTED")
#         print "Check..."#, dbVersion
#     except arcpy.ExecuteError as e:
#         print "Failed to create version:"
#         print repr(e)#"I/O error({0}): {1}".format(e.errno, e.strerror)
#         return False
#    arcpy.ChangeVersion_management("Nautical/CulturalFeaturesL", "TRANSACTIONAL", ""
    
    # we don't need Editor, startEditing and startOperation for file .gdbs
    # or if there are no FIX rules
    if connType == 1 and withEditSess:
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
#     utils.log("db = {}".format(db))
    
    return [db, edit]


def FinishUpDB(db, edit):
    """Reconcile and Post the version, and clean up."""
    
    utils.log("   < FinishUpDB() >")

    if edit is not None: # is there an active edit session
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

    utils.log("   < CheckData() >")
    
    hasEdits = False
    for rule in rules:
        if rule.dofix:
            hasEdits = True
    
    # Set up database connection and edit session
    try:
        db_str, db_editSess = SetUpDB(dataset, hasEdits)
    except Exception as exc:
        utils.log("Problem connecting to database, quitting.\n"+str(exc))
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

    utils.log("   < CheckTables() >")
    totalFixes = 0
    totalLogs = 0
    
    for rule in rules:
        print rule.id;
        if(rule.dofix): # FIX (no LOVE rules here)
            # v. 0.1:
            # print "UPDATE " + str(rule.fclist) + " SET " + rule.field + " = " + rule.fixvalue + " WHERE " + rule.GetWhereString()
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
                            logStr += "{} = {} (was {}), ".format(rule.fixLst[i][0], rule.fixLst[i][1], utils.encodeIfUnicode(row[defaultFieldsNum+i]))
                            fixVal = rule.fixLst[i][1] # set the update value
                            row[defaultFieldsNum+i] = fixVal
                            i += 1
                        logStr = logStr[0:-2] + " for OBJECTID = {} in {}".format(row[0], fc)
                        utils.log(logStr)
                        if not TEST_RULES_ONLY:
                            uc.updateRow(row) # do the actual update
                        pass
                utils.log("Total {} fix hits for rule {} ({})".format(count, rule.id, fc))
                totalFixes += count
        else: # LOG
            # v. 0.1:
            # print "SELECT FROM " + str(rule.fclist) + " WHERE " + rule.GetWhereString()
            for fc in rule.fclist:
                count = 0
                fields = ["OBJECTID", "LNAM"] + rule.fixLst # fields to get from the db, update log writing and reportValues below if this changes
                if (rule.mode == 'LOVE'):
                    fields.append(rule.condition[0]) # include the field we're testing
                try:
                    with arcpy.da.SearchCursor(dataset+fc, fields, where_clause=rule.GetWhereString()) as sc:
                        for row in sc:
                            reportValues = ''
                            if rule.fixLst:
                                for i,field in enumerate(rule.fixLst):
                                    reportValues += ', '+field+"="+utils.encodeIfUnicode(row[i+2])
                                    if field == 'FCSUBTYPE':
                                        reportValues += '/{}'.format(S57names.FCFCS2ABB(fc, str(row[i+2])))
                                reportValues = ' (' + reportValues[2:] + ')'
                            if(rule.mode == 'SQL'):
                                count += 1
                                utils.log("Found SQL rule {} violation ({}) for OBJECTID={} in {}{}"
                                    .format(rule.id, rule.title, row[0], fc, reportValues))
                            elif rule.mode == 'LOVE' :
                                for val in row[-1].split(','):
                                    if not val in rule.condition[1]:
                                        count += 1
                                        utils.log("Found LOVE rule {} violation ({}) for OBJECTID={} in {} ({}: {} in {}){}"
                                            .format(rule.id, rule.title, row[0], fc, rule.condition[0], val, row[-1], reportValues))
                                        break
                except Exception as err:
                    utils.log("Found error in rule {}, check SQL syntax (e.g. unknown fieldname or string field treated as number): {}.{}, {}".format(rule.id, fc, rule.fcsubtype, rule.GetWhereString()))
                    print err
                if count > 0:
                    utils.log("Total {} search hits for rule {} ({}: {}; WHERE {})".format(count, rule.id, fc, rule.title, rule.GetWhereString()))
                totalLogs += count
    utils.log("     Done checking tables, total {} log hits and {} fixes.".format(totalLogs, totalFixes))
    print "Done checking tables, total {} log hits and {} fixes.".format(totalLogs, totalFixes)

