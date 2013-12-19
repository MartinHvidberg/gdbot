
import arcpy

def ConnectToDB(db):    
    arcpy.env.workspace = db
    desDB = arcpy.Describe(db)
    if desDB.workspaceFactoryProgID == "esriDataSourcesGDB.SdeWorkspaceFactory.1":
        print "it's a SDE geodatabase"
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.FileGDBWorkspaceFactory.1":
        print "it's a File geodatabase"
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.AccessWorkspaceFactory.1":
        # it's a Personal geodatabase
        pass
    elif desDB.workspaceFactoryProgID == "esriDataSourcesGDB.InMemoryWorkspaceFactory.1":
        # it's a in_memory workspace
        pass
    elif desDB.workspaceFactoryProgID == "":
        # it's a Other (shapefile, coverage, CAD, VPF, and so on) 
        pass
    else: # It's not a recognizable DB
        pass
    
    return "the connection in some form...Where it's clear if it is versioned"


def main(db):
    
    # Read the .gdbot file and build the dictionary of bot-rules
    
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
    
    # Reconsile and Post the version, if allowed by the run mode
    
    # Stop the edit session
    
    # Remove the Version if Posted
    
    # Disconnect from db
    
    # Finish of logfiles, etc. and clean up nicely...
    
    
    return 0
    
if __name__ == "__main__":
    #db = "Database Connections\green2_nis@nis_editor.sde"
    db = "C:\Martin\Work_Eclipse\BuildGreen\data\input.gdb"
    main(db)    
else:
    print "Non recognized caller: "+__name__
