"""
    GDBOT - a Geodatabase (ro)bot
    The purpose of this project is to keep a geo data base clean and tidy
    The script acts based on a number of rules, the rules are stores in a .gdbot file
    
    Author: Martin Hvidberg <mahvi@gst.dk>
    Author: Hanne L. Petersen <halpe@gst.dk>
    
    SYNTAX:  gdbot.py rulefile logfile database_connection
        e.g. gdbot.py rules\nulls.gdbot logs\nulls.log nis_editor@green3.sde
    
    # Ver. 0.1: ; gdbot syntax version 1.0 (e.g. no Mode field, and different Condition syntax from 1.1)
    # Ver. 0.2: Fundamental changes to rule input format ; gdbot syntax version 1.1
    # Ver. 0.3: allowing FIX action to include a list of fields to report ; gdbot syntax version 1.2
    # Ver. 0.4: introducing LOVE (List Of Valid Elements) mode
    
    To do:
        - Allow checks for other fds than Nautical (separate mode?)
        
        - Allow to check in fc's  with wildcard matching names (e.g. like '%anno%')
    
        - Find out if we want to use versioning - changes still arrive in products without versions
        
        - Error handling:
          - catch failing updates and back out without posting - that should be what 'with' does already
          - detect problems with connection setup etc.
        
        - Polish log output format

        - Consider a MAIL action option, that will (log and) email the last editor

"""
import os, sys
from datetime import datetime # for datetime.now()

sys.path.append(r'\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\common') # TODO: use os.getcwd()...
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


def main(db, rulefile, logfile, mails):
    
    print "  Output goes to: "+logfile
    utils.log("  Current execute path: "+os.getcwd())
    print "Rulefile: "+rules
    print "Database connection: "+db
    if len(mails) == 0:
        print "No email."
    else:
        print "Email will be sent to: "+str(mails)
    
    timStart = datetime.now()
    
    # Read the .gdbot file and build the list of bot-rules
    lstRules = rule_parser.ReadRules(rulefile)
    #print lstRules
    
    if isinstance(lstRules, int): # if ReadRules returned a number, it's an error code...
        utils.log("ReadRules returned an error...")
        return lstRules

    print "Number of rules: "+str(len(lstRules))
    utils.log("  Checking {}, {} rules".format(rulefile, len(lstRules)))
    
    data_checker.CheckData(db, lstRules)

    timEnd = datetime.now()
    durRun = timEnd - timStart
    utils.log("   Total " + __file__ + " duration (h:mm:ss.dd): " + str(durRun)[:-3])
    
    # Finish off logfiles, etc. and clean up nicely...
    if len(logfile) > 0:
        utils.writeLogToFile(logfile)
    if len(mails) > 0:
        utils.sendLogToEmail(mails, 'gdbot run, {}'.format(rulefile.split('\\')[-1]), "Found")
    
    timEnd = datetime.now()
    durRun = timEnd - timStart
    print "\n   Total " + __file__ + " duration (h:mm:ss.dd): " + str(durRun)[:-3]

    return 0

def printHelp():
    print "python gdbot.py rulefile logfile connectionfile email"
    
if __name__ == "__main__":

    #RunGdbTests()

    #rules = r"\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\gdbot\rules\misc-gst-rules.gdbot"
    rules = r"\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\gdbot\rules\test.gdbot"
    #rules = r"\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\gdbot\rules\nulls-log.gdbot"

#    logfile = "log.txt"
    logfile = r"\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\gdbot\log.txt"

    db = r"\\hnas1evs2.kms.adroot.dk\vol4\KMS\o-kms\_TeamNIS_Produktion\BatchScripts\sde_filer\nis_editor@green3.sde"

    mails = []#['halpe@gst.dk']
    
    if (len(sys.argv)>1):
        rules = sys.argv[1]
    #else:
    #    printHelp()
    #    # exit or just run with default (test.gdbot)?
    #    exit # TODO: why does this not exit?
    
    if len(sys.argv) > 2:
        logfile = sys.argv[2]
    
    if len(sys.argv) > 3:
        db = sys.argv[3]
    
    if len(sys.argv) > 4:
        mails = sys.argv[4].split(',')

    #try:
    #    with PyCallGraph(output=GraphvizOutput()):
    #        print " *** Running in pycallgraph *** "
    #        main(db, rules, logfile, mails)
    #except: # TODO: only catch pycallgraph errors
    #    main(db, rules, logfile, mails)
    
    main(db, rules, logfile, mails)

else:
    print "Non-recognized caller: "+__name__
