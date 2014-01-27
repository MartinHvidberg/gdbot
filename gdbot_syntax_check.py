import sys

def note_error(strE):
    return ["Bad start: "+strE]

def check_compiler(strC):
    lstErrors = list()
    lstC = strC[1:].strip().split("=")
    lstKnownCompilers = ["file_title","file_type","gdbot_syntax_version","log_file","send_log_file","email_address"]
    if lstC[0].strip() in lstKnownCompilers:
        # gdbot version
        if lstC[0].strip() == "gdbot_syntax_version":
            if not lstC[1].strip().replace('.','',1).isdigit():
                lstErrors.append("Bad compiler. Bad gdbot ver.: "+lstC[1].strip())
        # log file
        if lstC[0].strip() == "log_file":
            if len(lstC[1].strip().replace('.','')) < 1:
                lstErrors.append("Bad compiler. Short logfile name: "+lstC[1].strip())
        # send log
        if lstC[0].strip() == "send_log_file":
            if lstC[1].strip().lower() not in ("true","false"):
                lstErrors.append("Bad compiler. Invalid send_log_boolean: "+lstC[1].strip())
        # email address
        if lstC[0].strip() == "email_address":
            if not "@" in lstC[1]:
                lstErrors.append("Bad compiler.  No valid email address: "+lstC[1].strip())
    else:
        lstErrors.append("Bad compiler: "+lstC[0].strip())
    return lstErrors

def check_gdbotrule(strR):
    lstErrors = list()
    lstR = strR[1:].strip().split(":")
    if len(lstR) == 9: # Valid length
        if lstR[0].strip().isdigit(): # Valid ID number
            lstLegalModes = ["SQL"]
            if lstR[2].strip() in lstLegalModes: # Valid Mode
                if True: # FC is valid
                    if True: # FCS is valid
                        if True: # SQL is valid
                            if lstR[6].strip().upper() in ("LOG","FIX"): # Action is valid
                                if True: # Action-SQL / Log-message is valid
                                    pass
                                else:
                                    lstErrors.append("Bad rule. Unknown Action-SQL / Log-message: "+strR)
                            else:
                                lstErrors.append("Bad rule. Unknown Action: "+strR)
                        else:
                            lstErrors.append("Bad rule. Invalid SQL: "+strR)
                    else:
                        lstErrors.append("Bad rule. Unknown Feature Class Subtype: "+strR)
                else:
                    lstErrors.append("Bad rule. Unknown Feature Class: "+strR)
            else:
                lstErrors.append("Bad rule. Unknown rule mode: "+strR)
        else:
            lstErrors.append("Bad rule. Rule ID not a number: "+strR)
    else:
        lstErrors.append("Bad rule. Not 9 tokens: "+strR)
    return lstErrors

def syntax_check(lstLines):
    # strip empty- and comment-lines, and EOL-marks
    lstRL = list()
    for strRL in lstLines:
        strRule = strRL[:strRL.find("#")].strip()
        if len(strRule) > 1:
            lstRL.append(strRule)
    # analyze lines
    lstErrors = list()
    for strRule in lstRL:
        if strRule[0] == "%":
            lstErrors.extend(check_compiler(strRule))
        elif strRule[0] == ":":
            lstErrors.extend(check_gdbotrule(strRule))
        else:
            lstErrors.extend(note_error(strRule))
    lstErrors = [x for x in lstErrors if x != ""]
    return lstErrors

if __name__ == "__main__":

    if len(sys.argv) >= 1:
        for fil in sys.argv[1:]: # Don't check the .py itself...
            print " Syntax check : ",fil
            # Open file
            filR = open(fil,"r")
            lstR = filR.readlines()
            # Run Syntax check
            x = syntax_check(lstR)
            print x
    else:
        print "Usage : gdbot_systax_check input.gdbot"
    
    
