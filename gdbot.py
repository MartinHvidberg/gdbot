"""
    GDBOT - a Geodatabase (ro)bot
    The purpose of this project is to keep a geo data base clean and tidy
    The script acts based on a number of rules, the rules are stores in a .gdbot file
    
    Author: Martin Hvidberg <mahvi@gst.dk>
    Author: Hanne L. Petersen <halpe@gst.dk>
    
    # Ver. 0.2: Fundamental changes to rule input format
    # Ver. 0.3: allowing FIX action to include a list of fields to report
    
    To do:
    
        - Find out if we want to use versioning - changes still arrive in products without versions
        
        - Error handling:
          - catch failing updates and back out without posting - that should be what 'with' does already
          - detect problems with connection setup etc.
        
        - Polish log output format

        - Consider a MAIL action option, that will (log and) email the last editor

"""
import os
from datetime import datetime # for datetime.now()
import arcpy

import utils
import rule_parser
import data_checker # comment this out to avoid importing arcpy

# for callgraph only
#from pycallgraph import PyCallGraph
#from pycallgraph.output import GraphvizOutput


def RunGdbTests():
    """Test on a file gdb to verify syntax and rule validity."""
    global logfilename
    logfilename = "test.log"
    readrules  = "./readtest.gdbot"
    checkrules = "./ruletest.gdbot"
    utils.log("*** Start GDBtest. "+str(datetime.now())+" ***")
    
    print "Starting read tests..."
    lst_rules = rule_parser.ReadRules(readrules)
    #print lst_rules
    for rule in lst_rules:
        print " Rule: "+rule.__repr__().strip()
    print "Finished read tests."
#     return
    
    lst_rules = []
    
    print "Starting check tests..."
    #dataset = "./clip_67_67_5_til_1411.gdb/"
    #dataset = "./1462hAndheld.gdb/"
    datazip = "../test.gdb.zip"
    dataset = ".\\"+datazip[3:-4]+"\\"
    try:
#         print "deleting test gdb..."
#         os.system("del /q %s" % (dataset))
#         print "extracting test gdb..."
#         os.system("unzip -q %s" % (datazip))
        # unzipping will produce an error:
        # test.gdb/:  ucsize 163840 <> csize 0 for STORED entry ; continuing with "compressed" size value
        # but seems to work fine anyway
        pass
    except BaseException as e:
        print "system command (delete/extract/...) failed: " + str(e)
    lst_rules = rule_parser.ReadRules(checkrules)
    print lst_rules
    data_checker.CheckData(dataset, lst_rules)
    print "Finished check tests."
    
    # TODO: compare the log file output to the expected output
    # 'C:\Program Files (x86)\WinMerge\WinMergeU.exe' ...
    # TODO: compare the resulting gdb to the expected result
    #writeLogToFile('log.txt')


def main(db, rulefile, logfile):
    
    timStart = datetime.now()
    # Read the .gdbot file and build the list of bot-rules
    lstRules = rule_parser.ReadRules(rulefile)
    #print lstRules
    
    if isinstance(lstRules, int): # if ReadRules returned a number, it's an error code...
        print "ReadRules returned an error..."
        return lstRules

    print "Number of rules: "+str(len(lstRules))
    
    data_checker.CheckData(db, lstRules)

    # Finish off logfiles, etc. and clean up nicely...
    utils.writeLogToFile('log.txt')
    
    timEnd = datetime.now()
    durRun = timEnd - timStart
    print "\n  Total " + __file__ + " duration (h:mm:ss.d): " + str(durRun)[:-3]

    return 0
    
    
if __name__ == "__main__":

    #RunGdbTests()

    #rules = "ruletest.gdbot"
    #rules = "test.gdbot"
    #rules = "M:/HAL/TeamNIS/Tools/PythonStuff/gdbot/rule_generators/nulls.gdbot"
    rules = "M:/HAL/TeamNIS/Tools/PythonStuff/gdbot/gst_rules/S5758.gdbot"
    
    db = "M:/HAL/TeamNIS/Tools/SDE_connections/Yellow3/nis_editor@yellow3.sde"
    #db = "M:/HAL/TeamNIS/Tools/SDE_connections/nis_editor@green3.sde"
    #db = "C:\Martin\Work_Eclipse\BuildGreen\data\input.gdb"
#     db = "./test.gdb"

    logfile = "log.txt"

    #try:
    #    with PyCallGraph(output=GraphvizOutput()):
    #        print " *** Running in pycallgraph *** "
    #        main(db, rules, logfile)
    #except: # TODO: only catch pycallgraph errors
    #    main(db, rules, logfile)
    
    main(db, rules, logfile)

else:
    print "Non-recognized caller: "+__name__
