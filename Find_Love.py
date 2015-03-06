'''
Find "List Of Valid Elements" cases in any field in any FC in NIS
Created on 31. July 2014
@author: mahvi@kms.dk / Martin@Hvidberg.net
'''

strName = "Find Love"
strVer = "1.0.0"
strBuild = "'140805"

### History
# Ver. 1.0.0 - First working version
#    Partly based on "gdbot_rc_domainvalidation.py
#    Remove '' from output love
#    Sort love as integers
# Ver. 1.0.1 - by halpe
#    Output file is now the gdbot file
#    Domains are read from the NIS, no longer hard-coded

### To do
# Look for XXX in the code

import sys
from datetime import datetime # for datetime.now()
import arcpy
import arcEC # My recycled Easy-arcpy helper functions

timStart = datetime.now()


# *** Main

arcEC.SetMsg("'"+strName+"' ver. "+strVer+" build "+strBuild,0)

# *** Manage input parameters ***
strFDS = r"Database Connections/nis_editor@green3.sde/NIS.Nautical"
strFileName = "validation.gdbot"

# ** Harvest strings from GUI
if arcpy.GetParameterAsText(0) != '':
    arcEC.SetMsg("GUI said",0)
    strFDS = arcpy.GetParameterAsText(0)
    strFileName = arcpy.GetParameterAsText(1)
arcEC.SetMsg("Input Feature dataset: "+strFDS,0)
arcEC.SetMsg("Output filename: "+strFileName,0)

# *** Open output file
arcpy.env.overwriteOutput = True
try:
    f = open(strFileName, 'w')
except IOError, e:
    print e.errno
    print e
    strErrorMessage = "Error - Can't open output file: "+strFileName+" system says: " + str(e.errno) + " : " + str(e)
    arcEC.SetMsg(strErrorMessage,2)
    sys.exit(strErrorMessage)

f.write("# Source: FindLove.py\n")
f.write("\n")
f.write("% file_title = Find Love\n")
f.write("% gdbot_syntax_version = N/A\n")
f.write("\n")
f.write("% log_file = \n")
f.write("% log_email = (mahvi@gst.dk, halpe@gst.dk) # Who to mail if I need human help\n\n")
f.write("\n")
f.write(": ruleID : ruleTitle : Mode : FC : FCsubtype : Condition : ActionType : Action : Comments)\n")

dicT = dict()

# *** Open DOMAIN ***
strConn = "Database Connections/nis_editor@green3.sde"
domains = arcpy.da.ListDomains(strConn)
dicDom = dict()
for domain in domains:
    codedVals = domain.codedValues
    try: # some have them as string
        del codedVals['-32767']
    except:
        pass
    try: # some have them as ints
        del codedVals[-32767]
    except:
        pass
    dicDom[domain.name] = codedVals


# *** Open FDS Descriptions ***
arcEC.SetMsg("Open Description",0)
dicDescribtion = arcpy.Describe(strFDS)

strReport  = ""
strReport += "\n   - catalog path: " + dicDescribtion.catalogPath
strReport += "\n   - name: " + dicDescribtion.name
strReport += "\n   - data type: " + dicDescribtion.dataType
strReport += "\n   - children expanded: " + str(dicDescribtion.childrenExpanded)
strReport += "\n   - children count: " + str(len(dicDescribtion.children))
arcEC.SetMsg(strReport,0)

if len(dicDescribtion.children) > 0:
    arcEC.SetMsg("   Analyzing Descriptions of layers: "+str(len(dicDescribtion.children)),0)
    numFCcounter = 0
    for dicChildDescribtion in dicDescribtion.children:
        numFCcounter += 1
        numFieldCounter = 0
        FCname = dicChildDescribtion.baseName # XXX remove 'NIS.' from here
        if FCname[:4] == "NIS.":
            FCname = FCname[4:]
        arcEC.SetMsg("\n====== FC ====== " + str(numFCcounter) + " of " + str(len(dicDescribtion.children)) + " ====== " + FCname + " =============", 0)
        for objField in dicChildDescribtion.fields:
            # Build dic of dic of (fieldtype/fieldname)
            ft = str(objField.type)
            fn = str(objField.name)
            if not ft in dicT.keys():
                dicT[ft] = dict()
            if not fn in dicT[ft].keys():
                dicT[ft][fn] = 1
            else:
                newCount = dicT[ft][fn] + 1
                dicT[ft][fn] = newCount
            numFieldCounter += 1
            # Look for Love in this field
            if objField.type in ("Geometry", "OID", "Blob","Date", "Double", "Guid", "Integer", "SmallInteger"): # Considered irrelevant, or can't hold love
                pass#arcEC.SetMsg(str(objField.name) + " type: "+ str(objField.type) + " ... Irrelevant!",0)
            elif objField.type in ("String"): # relevant!
                # =================================================================================================================
                # # S-57 - attribute type L (list)
                # * list (L): The expected input is a list of one or more numbers selected
                # from a list of pre-defined attribute values. Where more than one
                # value is used, they must normally be separated by commas but
                # in special cases slashes (/) may be used.
                # The abbreviation for this type is L.
                if objField.name in ("CATACH", "CATAIR", "CATBRG", "CATDPG", "CATHAF", "CATHLK", "CATLIT", "CATLMK", "CATLND", "CATMPA", "CATOFP", "CATPIP", "CATREA", "CATROS", "CATRSC", "CATSCF", "CATSIT", "CATSIW", "CATSPM", "CATVEG", "COLOUR", "COLPAT", "FUNCTN", "LITVIS", "NATCON", "NATQUA", "NATSUR", "PRODCT", "QUASOU", "RESTRN", "STATUS", "SURTYP", "TECSOU"):
                    #arcEC.SetMsg("  ====== Found L string ======" + str(objField.name),0)
                    if objField.domain != "":
                        arcEC.SetMsg(str(objField.name) + " ====== List field with Domain.",0)
                    else:
                        ### Handle LIST field without Esri-Domain, but with S-57 "list of valid elements"
                        if "NAUTICAL_"+objField.name in dicDom.keys():
                            lst_love = dicDom["NAUTICAL_"+objField.name].keys()
                            lst_love = sorted(lst_love, key=int)
                            str_love = str(lst_love).replace('\'','').replace('"','').replace('[','(').replace(']',')').replace(' ','').replace('u','') # CATHLK seems to come as miscoded unicode
                        else:
                            str_love = "()"
                        gdbot = ": 136-{0}-{1} : {2} field {3} violated S-57 list of valid elements : LOVE : {2} : * : {3} % {4} : LOG : FCSUBTYPE : ".format(("000"+str(numFCcounter))[-3:], ("000"+str(numFieldCounter))[-3:], FCname, objField.name, str_love)
                        f.write(gdbot+"\n")
                        arcEC.SetMsg(gdbot, 0)
                    continue
                # # S-57 - attribute type E (enumerated)
                # * enumerated (E): The expected input is a number selected from a list of
                # pre-defined attribute values. Exactly one value must be chosen.
                # The abbreviation for this type is E.
                elif objField.name in ("$JUSTH", "$JUSTV", "$SPACE", "$TINTS", "BCNSHP", "BOYSHP", "BUISHP", "CAT_TS", "CATBUA", "CATCAM", "CATCAN", "CATCBL", "CATCHP", "CATCOA", "CATCON", "CATCOV", "CATCRN", "CATCTR", "CATDAM", "CATDIS", "CATDOC", "CATFIF", "CATFNC", "CATFOG", "CATFOR", "CATFRY", "CATGAT", "CATICE", "CATINB", "CATLAM", "CATMFA", "CATMOR", "CATNAV", "CATOBS", "CATOLB", "CATPIL", "CATPLE", "CATPRA", "CATPYL", "CATQUA", "CATRAS", "CATROD", "CATRTB", "CATRUN", "CATSEA", "CATSIL", "CATSLC", "CATSLO", "CATTRK", "CATTSS", "CATWAT", "CATWED", "CATWRK", "CATZOC", "CATZOC-ED31", "CONDTN", "CONRAD", "CONVIS", "DUNITS", "EXCLIT", "EXPSOU", "HORDAT", "HUNITS", "JRSDTN", "LITCHR", "MARSYS", "PUNITS", "QUAPOS", "SIGGEN", "T_ACWL", "T_MTOD", "TOPSHP", "TRAFIC", "VERDAT", "WATLEV"):
                    continue
                # # S-57 - attribute type F (float)
                # * float (F): The expected input is a floating point numeric value with defined range, resolution, units and format.
                #  The abbreviation for this type is F.
                elif objField.name in ("$CSIZE", "$SCALE", "BURDEP", "CURVEL", "DRVAL1", "DRVAL2", "ELEVAT", "ESTRNG", "HEIGHT", "HORACC", "HORCLR", "HORLEN", "HORWID", "ICEFAC", "LIFCAP", "ORIENT", "POSACC", "RADIUS", "SECTR1", "SECTR2", "SIGPER", "SOUACC", "VALACM", "VALDCO", "VALLMA", "VALMAG", "VALMXR", "VALNMR", "VALSOU", "VERACC", "VERCCL", "VERCLR", "VERCOP", "VERCSA", "VERLEN"): # ...
                    continue
                # # S-57 - attribute type I (integer)
                # * integer (I): The expected input is an integer numeric value with defined range, units and format.
                # The abbreviation for this type is I.
                elif objField.name in ("CSCALE", "MLTYLT", "SCAMAX", "SCAMIN", "SCVAL1", "SCVAL2", "SDISMN", "SDISMX", "SIGFRQ", "T_TINT"):
                    continue
                # # S-57 - attribute type A (coded string)
                elif objField.name in ("$CHARS", "$SCODE", "AGENCY", "COMCHA", "CPDATE", "DATEND", "DATSTA", "NATION", "NMDATE", "PEREND", "PERSTA", "PRCTRY", "RADWAL", "RECDAT", "RECIND", "RYRMGV", "SHIPAM", "SIGGRP", "SIGSEQ", "SORDAT", "SORIND", "SUREND", "SURSTA", "T_HWLW", "T_THDF", "T_TSVL", "T_VAHC", "TIMEND", "TIMSTA", "TS_TSP", "TS_TSV"):
                    continue
                # # S-57 - attribute type S ()
                # * free text (S): The expected input is a free-format alphanumeric string.
                # It may be a file name which points to a text or graphic file.
                # The abbreviation for this type is S.
                elif objField.name in ("$NTXST", "$TXSTR", "CALSGN", "CLSDEF", "CLSNAM", "INFORM", "NINFOM", "NOBJNM", "NPLDST", "NTXTDS", "OBJNAM", "PICREP", "PILDST", "PUBREF", "SURATH", "SYMINS", "TXTDSC"):
                    continue
                #  # Known Esri fields, i.e. Not S-57.
                elif objField.name in ("DELETE_COMMENT", "EDITOR", "EDITOR_COMMENT", "NIS_EDITOR", "NIS_EDITOR_COMMENT", "NIS_VERIFIER", "PARENTID", "VERIFIER"):
                    continue
                #  # Known GST fields, i.e. Not S-57.
                elif objField.name in ("GST_LINTXT", "GST_NID"):
                    continue
                #  # Known fields with unknown decent. XXX <--- Have Esri explain these XXX
                elif objField.name in ("DSNM", "LNAM", "MAPID", "NAME", "NOID", "VI_NAME"):
                    continue
                # =================================================================================================================
                else:
                    arcEC.SetMsg(str(objField.name) + " ... Should this be checked ?",0)
            else: # Unexpected field type
                arcEC.SetMsg("Unexpected field type found: " + str(objField.type) + "Field: " + str(objField.name) + " in " + dicChildDescribtion.baseName, 1)
        else:
            pass#arcEC.SetMsg(" Field have domain: " + objField.name,0)
else:
    arcEC.SetMsg("No Feature Layers found",2)


#for ftype in dicT.keys():
#    for fname in dicT[ftype].keys():
#        f.write(str(ftype) + "\t " + str(fname) + " \t " + str(dicT[str(ftype)][str(fname)]) + "\n")


# *** All Done - Cleaning up ***
f.close()
timEnd = datetime.now()
durRun = timEnd-timStart
arcEC.SetMsg("Python stript duration (h:mm:ss.dddddd): "+str(durRun),0)

# *** End of Script ***

# Music that accompanied the coding of this script:
#   AC/DC - Back in Black
#   Bob Marley - No woman, no cry
