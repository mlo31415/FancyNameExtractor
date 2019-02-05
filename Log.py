
#=============================================================================
# Print the text to a log file open by the main program
# If isError is set also print it to the error file.
def Log(text, isError=False):
    global g_logFile
    global g_errorFile
    global g_logHeader
    global g_logErrorHeader

    # If this is the first log entry for this header, print it and then clear it so it's not printed again
    if g_logHeader is not None:
        print(g_logHeader)
        print("\n"+g_logHeader, file=g_logFile)
    g_logHeader=None

    if isError:
        # If this and error entry and is the first error entry for this header, print it and then clear it so it's not printed again
        if g_logErrorHeader is not None:
            print("----\n"+g_logErrorHeader, file=g_errorFile)
        g_logErrorHeader=None

    # Print the log entry itself
    print(text)
    print(text, file=g_logFile)
    if isError:
        print(text, file=g_errorFile)

# Set the header for any subsequent log entries
# Note that this header will only be printed once, and then only if there has been a log entry
def LogSetFanzine(name):
    global g_logHeader
    global g_logErrorHeader
    global g_logLastFanzine

    if g_logLastFanzine is None or name != g_logLastFanzine:
        g_logHeader=name
        g_logErrorHeader=name
        g_logLastFanzine=name


def LogOpen(logfilename, errorfilename):
    global g_logFile
    g_logFile=open(logfilename, "w+")

    global g_errorFile
    g_errorFile=open(errorfilename, "w+")

    global g_logHeader
    g_logHeader=None
    global g_logErrorHeader
    g_logErrorHeader=None
    global g_logLastFanzine
    g_logLastFanzine=None


def LogClose():
    global g_logFile
    g_logFile.close()
    global g_errorFile
    g_errorFile.close()