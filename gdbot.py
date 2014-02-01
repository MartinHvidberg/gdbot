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
import os
from datetime import datetime # for datetime.now()

import utils
import rule_parser
import data_checker # comment this out to avoid importing arcpy


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
    
    # Read the .gdbot file and build the list of bot-rules
    lstRules = rule_parser.ReadRules(rulefile)
    
    data_checker.CheckData(db, lstRules)    
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
