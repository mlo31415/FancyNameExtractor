from __future__ import annotations
from typing import Optional, Dict, Set, List

import os
import re
from datetime import datetime

from F3Page import F3Page, DigestPage
from Log import Log, LogOpen, LogSetHeader
from HelpersPackage import SplitOnSpan, WindowsFilenameToWikiPagename, WikiExtractLink, FindIndexOfStringInList
from FanzineIssueSpecPackage import FanzineDateRange

# The goal of this program is to produce an index to all of the names on Fancy 3 and fanac.org with links to everything interesting about them.
# We'll construct a master list of names with a preferred name and zero or more variants.
# This master list will be derived from Fancy with additions from fanac.org
# The list of interesting links will include all links in Fancy 3, and all non-housekeeping links in fanac.org
#   A housekeeping link is one where someone is credited as a photographer or having done scanning or the like
# The links will be sorted by importance
#   This may be no more than putting the Fancy 3 article first, links to fanzines they edited next, and everything else after that

# The strategy is to start with Fancy 3 and get that working, then bring in fanac.org.
# This program produces a comprehensive index on Fancy 3, including a list of all people names n Fancy 3.
# This is written to files which are used as input to the indexer for Fanac.org which produces the final result.

# We'll work entirely on the local copies of the two sites.

# For Fancy 3 on MediaWiki, there are many names to keep track of for each page:
#       The actual, real-world name.  But this can't always be used for a filename on Windows or a page name in Mediawiki, so:
#       WikiPagename -- the name of the MediaWiki page it was created with.
#       DisplayName -- The name that appears on the page. It may have been over-ridden using DISPLAYTITLE
#       URLname -- the name of the Mediawiki page in a URL
#                       Basically, spaces are replaced by underscores and the first character is always UC.  #TODO: What about colons? Other special characters?
#       WindowsFilename -- the name of the Windows file in the in the local site: converted using methods in HelperPackage. These names can be derived from the Mediawiki page name and vice-versa.
#
#       The URLname and WindowsFilename can be derived from the WikiPagename, but not necessarily vice-versa

fancySitePath=r"C:\Users\mlo\Documents\usr\Fancyclopedia\Python\site"   # A local copy of the site maintained by FancyDownloader
LogOpen("Log.txt", "Log Error.txt")

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folder named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
Log("***Querying the local copy of Fancy 3 to create a list of all Fancyclopedia pages")
Log("   path='"+fancySitePath+"'")
allFancy3PagesFnames = [f[:-4] for f in os.listdir(fancySitePath) if os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]
allFancy3PagesFnames = [cn for cn in allFancy3PagesFnames if not cn.startswith("index_")]     # Drop index pages
#allFancy3PagesFnames= [f for f in allFancy3PagesFnames if f[0:6].lower() == "windyc" or f[0:5].lower() == "new z"]        # Just to cut down the number of pages for debugging purposes
#llFancy3PagesFnames= [f for f in allFancy3PagesFnames if f[0:6].lower() == "plokta"]        # Just to cut down the number of pages for debugging purposes
Log("   "+str(len(allFancy3PagesFnames))+" pages found")

fancyPagesDictByWikiname={}     # Key is page's canname; Val is a FancyPage class containing all the references on the page

ignoredPagePrefixes=["Template;colon;", "Log 202"]
ignoredPages=["Standards", "Admin"]

Log("***Reading local copies of pages and scanning for links")
for pageFname in allFancy3PagesFnames:
    if pageFname not in ignoredPages:
        if all(pageFname.startswith(s) is False for s in ignoredPagePrefixes):
            val=DigestPage(fancySitePath, pageFname)
            if val is not None:
                fancyPagesDictByWikiname[val.Name]=val
            # Print a progress indicator
            l=len(fancyPagesDictByWikiname)
            if l%1000 == 0:
                if l > 1000:
                    Log("--",noNewLine=True)
                if l%20000 == 0:
                    Log("")
                Log(str(l), noNewLine=True)

Log("\n   "+str(len(fancyPagesDictByWikiname))+" semi-unique links found")

Log("Build the redirects table")
g_canonicalNames={}
for val in fancyPagesDictByWikiname.values():
    if val.IsRedirectpage:
        g_canonicalNames[val.Name]=val.Redirect
    else:
        g_canonicalNames[val.Name]=val.Name

# Build a locale database
Log("\n\n***Building a locale dictionary")
locales=set()  # We use a set to eliminate duplicates and to speed checks
for page in fancyPagesDictByWikiname.values():
    if "Locale" in page.Tags:
        LogSetHeader("Processing Locale "+page.Name)
        locales.add(page.Name)
    else:
        if page.UltimateRedirect is not None and page.UltimateRedirect in fancyPagesDictByWikiname.keys():
            if "Locale" in fancyPagesDictByWikiname[page.UltimateRedirect].Tags:
                LogSetHeader("Processing Locale "+page.Name)
                locales.add(page.Name)


# Convert names like "Chicago" to "Chicago, IL"
# We look through the locales database for names that are proper extensions of the input name
# First create the dictionary we'll need
localeBaseForms={}  # It's defined as a dictionary with the value being the base form of the key
for locale in locales:
    # Look for names of the form Name,ST
    m=re.match("^([A-Za-z .]*),\s([A-Z]{2})$", locale)
    if m is not None:
        city=m.groups()[0]
        state=m.groups()[1]
        if city not in localeBaseForms.keys():
            localeBaseForms[city]=city+", "+state
i=0
def BaseFormOfLocaleName(localeBaseForms: Dict[str, str], name: str) -> str:
    if name in localeBaseForms.keys():
        return localeBaseForms[name]
    return name


# Look for a pattern of the form:
#   Word, XX
#   where Word is a string of letters with an initial capital, the comma is optional, and XX is a pair of upper case letters
# Note that this will also pick up roman-numeraled con names, E.g., Fantasycon XI, so we need to remove these later
def ScanForLocales(locales: Set[str], s: str) -> Optional[Set[str]]:
    pattern="in (?:[A-Za-z]* )?\[*([A-Z][a-z]+\]*,?\\s+\[*[A-Z]{2})\]*[^a-zA-Z]"
            # (?:[A-Za-z]* )?   lets us ignore the "Oklahoma" of in Oklahoma City, OK)
            # \[*  and  \]*     Lets us ignore [[brackets]]
            # The "[^a-zA-Z]"   prohibits another letter following the putative state

    # We test for characters on either side of the name, so make sure there are some... #TODO handle this more cleanly
    lst=re.findall(pattern, " "+s+" ")
    impossiblestates={"SF", "MC", "PR", "II", "IV", "VI", "IX", "XI", "XX", "VL", "XL", "LI", "LV", "LX"}       # PR: Pogress Report; others Roman numerals
    skippers={"Astra", "Con"}       # Second word of multi-word con names
    out=set()
    for l in lst:
        l=l.replace("[", "")    # We only need to remove the [ because only a [ can be inside the capture group
        splt=SplitOnSpan(",\s", l)
        if len(splt) == 2:
            if splt[0] not in skippers and splt[1] not in impossiblestates:
                out.add(l)
        else:
            Log("...Split does not find two values: "+l)

    # That didn't work. Let's try country names that are spelled out.
    # We'll look for a country name preceded by a Capitalized word
    countries=["Australia", "New Zealand", "Canada", "Holland", "Netherlands", "Italy", "Gemany", "Norway", "Sweden", "Finland", "China", "Japan", "France", "Belgium",
               "Poland", "Bulgaria", "Israel", "Russia", "Scotland", "Wales", "England", "Ireland"]
    for country in countries:
        if country in s:
            loc=s.find(country)
            splt=SplitOnSpan(",\s\[\]", s[:loc]) # Split on spans of "," and space
            if len(splt) > 1:
                if splt[-2:-1][0] == "in":  # 2nd last token is "in"
                    name=splt[-1:][0]
                    if re.match("[A-Z]{1}[a-z]+$", name):
                        out.add(name+", "+country)

    # Look for the pattern "in [[City Name]]"
    pattern="in \[\[((?:[A-Z][A-Za-z]+[\.,]?\s*)+)\]\]"
            # Capture "in" followed by "[[" followed by a group
            # The group is a possibly repeated non-capturing group
            #       which is a UC letter followed by one or more letters followed by an option period or comma followed by zero or more spaces
            # ending with "]]"
    lst=re.findall(pattern, s)
    for l in lst:
        out.add(BaseFormOfLocaleName(localeBaseForms, l))
    return out


#------------------------------------
# Just a simple class to conveniently wrap a bunch of data
class ConInfo:
    def __init__(self, Link: str="", Text: str="", Loc: str="", DateRange: FanzineDateRange=FanzineDateRange(), Virtual: bool=False, Cancelled: bool=False):
        self.Link: str=Link  # The actual text of the link on the series page
        self.Text: str=Text  # The displayed text for that link on the series page
        self.Loc: str=Loc
        self.DateRange: FanzineDateRange=DateRange
        self.Virtual: bool=Virtual
        self.Cancelled: bool=Cancelled

    def __str__(self) -> str:
        s=self.Link+" "+self.Text+" "+str(self.DateRange)+" "+self.Loc
        if self.Cancelled:
            s+=" cancelled=True"
        if self.Virtual:
            s+=" virtual=True"
        return s

    @property
    def CannonicalName(self) -> str:
        return CanonicalName(self.Link)


Log("***Analyzing convention series tables")

# Is at least one item in inputlist also in checklist?
def Crosscheck(inputList, checkList) -> bool:
    ListofHits=[FindIndexOfStringInList(checkList, x) for x in inputList]
    n=next((item for item in ListofHits if item is not None), None)
    return n

# Form the key used for the convention dictionary
def ConKey(conname: str, condate: FanzineDateRange) -> str:
    return conname#.lower()#+"$"+str(condate._startdate.Year)

def CanonicalName(name: str) -> str:
    if name is None or name == "":
        return ""
    assert len(g_cannonicalNames) > 0
    if name not in g_cannonicalNames.keys():
        Log("CannonicalName error: '"+name+"' for found in cannonicalNames")
        return name
    return g_canonicalNames[name]

def ConAdd(conlist: Dict[str], conname: str, condate: FanzineDateRange, val: ConInfo) -> None:
    conname=CanonicalName(conname)
    key=ConKey(conname, condate)
    if key in conlist.keys():
        old=conlist[key]
        if val.Loc != old.Loc and val.Link != old.Link:
            Log("ConKey: '"+key+"' already in conlist", isError=True)
            Log("   old="+str(old), isError=True)
            Log("   new="+str(val), isError=True)
    conlist[key]=val

# Create a dictionary of conventions with useful information about them.
# The key is the Wiki name of the convention instance page
# The value is a ConInfo structure which holds a bunch of useful info
conventions={}
for page in fancyPagesDictByWikiname.values():

    # First, see if this is a Conseries page
    if "Conseries" in page.Tags:
        LogSetHeader("Processing "+page.Name)
        # We'd like to find the columns containing:
        locColumn=None     # The convention's location
        conColumn=None     # The convention's name
        dateColumn=None    # The conventions dates
        for table in page.Table:
            LogSetHeader("Processing conseries "+page.Name)

            listLocationHeaders=["Location"]
            locColumn=Crosscheck(listLocationHeaders, table.Headers)
            # We don't log a missing location column because that is common and not an error

            listNameHeaders=["Convention", "Convention Name", "Name"]
            conColumn=Crosscheck(listNameHeaders, table.Headers)
            if conColumn is None:
                Log("***Can't find convention column in conseries page "+page.Name, isError=True)

            listDateHeaders=["Date", "Dates"]
            dateColumn=Crosscheck(listDateHeaders, table.Headers)
            if conColumn is None:
                Log("***Can't find Dates' column in conseries page "+page.Name, isError=True)

            if conColumn is not None and dateColumn is not None:

                # Walk the convention table, extracting the individual conventions
                # (Sometimes there will be multiple table
                if table.Rows is None:
                    Log("***Table has no rows: "+page.Name, isError=True)
                    continue
                for row in table.Rows:

                    # Look for a text flag indicating that the convention was held virtually or was cancelled
                    virtual=False
                    vPat=re.compile("[(]?(?:virtual|online|held online|moved online)[)]?", re.IGNORECASE)
                    cPat=re.compile("[(]?cancelled[)]?", re.IGNORECASE)
                    for index, col in enumerate(row):
                        # If this is the convention column, we don't want to remove the virtual designation because it's sometimes used as part of the con's name
                        if conColumn is not None and index == conColumn:
                            m=vPat.match(col)
                            if m is not None:
                                virtual=True
                        else:
                            # But for other columns, we want to remove the designation as it will just confuse later processing.
                            newcol=vPat.sub("", col)
                            if col != newcol:
                                virtual=True
                                row[index]=newcol
                                col=newcol
                        # Now check for a cancelled flag
                        newcol=cPat.sub("", col)
                        if col != newcol:
                            cancelled=True
                            row[index]=newcol
                            col=newcol

                    # If the con series table has a location, extract it
                    conloc=""
                    if conColumn is not None and locColumn is not None:
                        if locColumn < len(row) and len(row[locColumn]) > 0 and conColumn < len(row) and len(row[conColumn]) > 0:
                            con=WikiExtractLink(row[conColumn])
                            loc=WikiExtractLink(row[locColumn])
                            conloc=BaseFormOfLocaleName(localeBaseForms, loc)
                            Log("   Conseries: "+con+" is at " + conloc)

                    # If the conseries has a date, add the convention to the list
                    if conColumn < len(row) and len(row[conColumn]) > 0  and dateColumn < len(row) and len(row[dateColumn]) > 0:
                        # Ignore anything in trailing parenthesis
                        p=re.compile("\(.*\)\s?$")
                        datestr=p.sub("", row[dateColumn])
                        # Convert the HTML characters some people have inserted into their ascii equivalents
                        datestr=datestr.replace("&nbsp;", " ").replace("&#8209;", "-")

                        # Now look for dates. There are three cases to consider:
                        #1: date                    A simple date
                        #2: <s>date</s>             A canceled con's date
                        #3: <s>date</s> date        A rescheduled con's date
                        #4: <s>date</s> <s>date</s> A rescheduled and then cancelled con's dates
                        m=re.match("^\s?(?:<s>(.+?)</s>)?\s?(?:<s>(.+?)</s>)?\s?(.*)$", datestr)
                        if m is None:
                            Log("Date errror: "+datestr)
                            continue

                        fdr=[None, None, None]
                        for i in range(3):
                            if (m.groups()[i] is not None and len(m.groups()[i])) > 0:
                                fdr[i]=FanzineDateRange().Match(m.groups()[i])
                                if fdr[i].Duration() > 6:
                                    Log("??? "+page.Name+" has long duration: "+str(fdr[i]), isError=True)

                        # There should be at least one interpretable date range
                        if all(x is None for x in fdr) or all(x is None or (x is not None and x.IsEmpty()) for x in fdr):
                            Log("***Could not interpret "+row[conColumn]+"'s date range: "+row[dateColumn], isError=True)
                            continue

                        # Get the convention name
                        # [[xxx]]
                        # [[xxx|yyy]]               Use just xxx
                        # [[xxx|yyy]]: zzz          Ignore the ": "zzz"
                        # (Ignore <s>...</s> if present.)
                        conname=row[conColumn].replace("<s>", "").replace("</s>", "")
                        conname=conname.replace("[[", "@@").replace("]]", "%%")  # The square brackets are Regex special characters. This makes the pattern simpler
                        # Match ''[['' then <stuff> then maybe '|' followed by <stuff> then ']]' then maybe (':' followed by styff) then EOL
                        m=re.match("@@([^|%]+)(\|?)([^%]*)%%(:?.*)$", conname)
                        if m is not None:
                            conname=m.groups()[0]
                        conname=CannonicalName(conname) # Convert to the connonical name

                        # There will be at most two dates, and at most one that is not cancelled
                        # So we have the following possibilities: (d), (d, dc1), (dc1), (dc1, dc2)
                        # Now add the convention entries
                        if fdr[0] is not None and not fdr[0].IsEmpty():
                            ConAdd(conventions, conname, fdr[0], ConInfo(Link=conname, Text=row[conColumn], Loc=conloc, DateRange=fdr[0], Virtual=virtual, Cancelled=True))      # We merge conventions with the same name and year
                        if fdr[1] is not None and not fdr[1].IsEmpty():
                            ConAdd(conventions, conname, fdr[1], ConInfo(Link=conname, Text=row[conColumn], Loc=conloc, DateRange=fdr[1], Virtual=virtual, Cancelled=True))      # We merge conventions with the same name and year
                        if fdr[2] is not None and not fdr[2].IsEmpty():
                            ConAdd(conventions, conname, fdr[2], ConInfo(Link=conname, Text=row[conColumn], Loc=conloc, DateRange=fdr[2], Virtual=virtual))      # We merge conventions with the same name and year

# OK, all of the con series have been mined.  Now let's look through all the con instances and see if we can get more location information from them.
# (Not all con series tables contain location information.)
# Generate a report of cases where we have non-identical con information from both sources.
with open("Con location discrepancies.txt", "w+", encoding='utf-8') as f:
    for page in fancyPagesDictByWikiname.values():
        # If it's an individual convention page, we search through its text for something that looks like a placename.
        if "Convention" in page.Tags and "Conseries" not in page.Tags:
            m=ScanForLocales(locales, page.Source)
            if m is not None:
                for place in m:
                    place=WikiExtractLink(place)
                    # Find the convention in the conventions dictionary and add the location if appropriate.
                    conname=CanonicalName(page.Name)
                    conkey=ConKey(conname, FanzineDateRange())
                    if conkey not in conventions.keys():
                        Log("Convention "+conkey+" not in Conseries",isError=True)
                        continue
                    old=conventions[conkey]
                    if place != old.Loc:
                        if old.Loc == "":   # If there previously was no location from the con series page, substitute what we found in the con instance page
                            old.Loc=place
                            continue
                        f.write(conname+": Location mismatch: '"+place+"' != '"+old.Loc+"'\n")


# Convert the con dictionary to a list and sort it in date order
conventions=[c for c in conventions.values()]
conventions.sort(key=lambda d: d.DateRange)

# The current algorithm messes up multi-word city names and only catches the last word.
# Correct the ones we know of to the full name.
corrections={
    "Angeles, CA": "Los Angeles, CA",
    "Antonio, TX": "San Antonio, TX",
    "Beach, CA": "Long Beach, CA",
    "Beach, FL": "West Palm Beaach, FL",
    "Bend, IN": "South Bend, IN",
    "Brook, LI": "Stony Brook, NY",
    "Brook, NY": "Stony Brook, NY",
    "Carrollton, MD": "New Carrollton, MD",
    "City, IA": "Iowa City, IA",
    "City, MO": "Kansas City, MO",
    "City, OK": "Oklahoma City, OK",
    "Collins, CO": "Fort Collins, CO",
    "Creek, MI": "Battle Creek, MI",
    "Diego, CA": "San Diego, CA",
    "Hill, NJ": "Cherry Hill, NJ",
    "Island, NY": "Long Island, NY",
    "Juan, PR": "San Juan, PR",
    "Lake, OH": "Indian Lake, OH",
    "Louis, MO": "St. Louis, MO",
    "Luzerne, NY": "Lake Luzerne, NY",
    "Mateo, CA": "San Mateo, CA",
    "Moines, IA": "Des Moines, IA",
    "Orleans, LA": "New Orleans, LA",
    "Paso, TX": "El Paso, TX",
    "Paul, MN": "St. Paul, MN",
    "Petersburg, FL": "St. Petersburg, FL",
    "Rosa, CA": "Santa Rosa, CA",
    "Spring, MD": "Silver Spring, MD",
    "Springs, CO": "Colorado Springs, CO",
    "Springs, NY": "Saratoga Springs, NY",
    "Station, TX": "College Station, TX",
    "Town, NY": "Rye Town, NY",
    "York, NY": "New York, NY"
}

#TODO: Add a list of keywords to find and remove.  E.g. "Astra RR" ("Ad Astra XI")

# Strip the convention names from the locations list.  (I.e., "Fantaycon XI" may look like a place, but it isn't.)
# We need a list of convention names.  These names are in [[name]] or [[name|name2]] for, so remove the crud
# connames=[c.Link.replace("[[", "").replace("]]","") for c in conventions]
# for conname, conlocs in conventionLocations.items():
#     newlocs=set()
#     for loc in conlocs:
#         if loc in corrections.keys():
#             loc=corrections[loc]
#         if loc not in connames:
#             newlocs.add(loc)
#     conventionLocations[conname]=newlocs

# ...
Log("Writing Convention timeline (Fancy).txt")
with open("Convention timeline (Fancy).txt", "w+", encoding='utf-8') as f:
    f.write("This is a chronological list of SF conventions automatically extracted from Fancyclopedia 3\n\n")
    f.write("If a convention is missing from the list, it may be due to it having been added only recently, (this list was generated ")
    f.write(datetime.now().strftime("%A %B %d, %Y  %I:%M:%S %p")+" EST)")
    f.write(" or because we do not yet have information on the convention or because the convention's listing in Fancy 3 is a bit odd ")
    f.write("and the program which creates this list isn't recognizing it.  In any case, we welcome help making it more complete!\n\n")
    f.write("The list currently has "+str(len(conventions))+" conventions.\n")
    currentYear=None
    currentDateRange=None
    # We're going to write a Fancy 3 wiki table
    # Two columns: Daterange and convention name and location
    # The date is not repeated when it is the same
    # The con name and location is crossed out when it was cancelled or moved and (virtual) is added when it was virtual
    f.write("<tab>\n")
    for con in conventions:
        conname=con.Link
        # Look up the location for this convention
        conloctext=con.Loc

        # Format the convention name and location for tabular output
        context=str(con.Text)
        if con.Cancelled:
            context="<s>"+context+"</s>"
        if con.Virtual:
            context+=" (virtual)"
        else:
            if len(conloctext) > 0:
                context+="&nbsp;&nbsp;&nbsp;<small>("+conloctext+")</small>"

        # Now write the line
        # We do a year header for each new year, so we need to detect when the current year changes
        if currentYear == con.DateRange._startdate.Year:
            if currentDateRange == con.DateRange:
                f.write("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' ' ||"+context+"\n")
            else:
                if con.Cancelled:
                    f.write("<s>"+str(con.DateRange)+"</s>||<s>"+context+"</s>\n")
                else:
                    f.write(str(con.DateRange)+"||"+context+"\n")
                currentDateRange=con.DateRange
        else:
            # When the current date range changes, we put the new date range in the 1st column of the table
            currentYear = con.DateRange._startdate.Year
            currentDateRange=con.DateRange
            f.write('colspan="2"| '+"<big><big>'''"+str(currentYear)+"'''</big></big>\n")
            if con.Cancelled:
                f.write("<s>"+str(con.DateRange)+"</s>||<s>"+context+"</s>\n")
            else:
                f.write(str(con.DateRange)+"||"+context+"\n")
    f.write("</tab>")
    f.write("{{conrunning}}\n[[Category:List]]\n")

# ...
# OK, now we have a dictionary of all the pages on Fancy 3, which contains all of their outgoing links
# Build up a dictionary of redirects.  It is indexed by the canonical name of a page and the value is the canonical name of the ultimate redirect
# Build up an inverse list of all the pages that redirect *to* a given page, also indexed by the page's canonical name. The value here is a list of canonical names.
Log("***Create inverse redirects tables")
redirects={}            # Key is the name of a redirect; value is the ultimate destination
inverseRedirects={}     # Key is the name of a destination page, value is a list of names of pages that redirect to it
for fancyPage in fancyPagesDictByWikiname.values():
    if fancyPage.Redirect is not None:
        redirects[fancyPage.Name]=fancyPage.UltimateRedirect
        if fancyPage.Redirect not in inverseRedirects.keys():
            inverseRedirects[fancyPage.Redirect]=[]
        inverseRedirects[fancyPage.Redirect].append(fancyPage.Name)
        if fancyPage.UltimateRedirect not in inverseRedirects.keys():
            inverseRedirects[fancyPage.UltimateRedirect]=[]
        if fancyPage.UltimateRedirect != fancyPage.Redirect:
            inverseRedirects[fancyPage.UltimateRedirect].append(fancyPage.Name)

# Analyze the Locales
# Create a list of things that redirect to a Locale, but are not tagged as a locale.
Log("***Look for things that redirect to a Locale, but are not tagged as a Locale")
with open("Untagged locales.txt", "w+", encoding='utf-8') as f:
    for fancyPage in fancyPagesDictByWikiname.values():
        if "Locale" in fancyPage.Tags:                        # We only care about locales
            if fancyPage.UltimateRedirect == fancyPage.Name:        # We only care about the ultimate redirect
                if fancyPage.Name in inverseRedirects.keys():
                    for inverse in inverseRedirects[fancyPage.Name]:    # Look at everything that redirects to this
                        if "Locale" not in fancyPagesDictByWikiname[inverse].Tags:
                            if "-" not in inverse:                  # If there's a hyphen, it's probably a Wikidot redirect
                                if inverse[1:] != inverse[1:].lower() and " " in inverse:   # There's a capital letter after the 1st and also a space
                                    f.write(fancyPage.Name+" is pointed to by "+inverse+" which is not a Locale\n")

# ...
# Create a dictionary of page references for people pages.
# The key is a page's canonical name; the value is a list of pages at which they are referenced.

# First locate all the people and create empty entries for them
peopleReferences={}
Log("***Creating dict of people references")
for fancyPage in fancyPagesDictByWikiname.values():
    if fancyPage.IsPerson():
        if fancyPage.Name not in peopleReferences.keys():
            peopleReferences[fancyPage.Name]=[]

# Now go through all outgoing references on the pages and add those which reference a person to that person's list
for fancyPage in fancyPagesDictByWikiname.values():
    if fancyPage.OutgoingReferences is not None:
        for outRef in fancyPage.OutgoingReferences:
            if outRef.LinkWikiName in peopleReferences.keys():    # So it's a people
                peopleReferences[outRef.LinkWikiName].append(fancyPage.Name)

# ...
Log("***Writing reports")
# Write out a file containing canonical names, each with a list of pages which refer to it.
# The format will be
#     **<canonical name>
#     <referring page>
#     <referring page>
#     ...
#     **<cannonical name>
#     ...
Log("Writing: Referring pages.txt")
with open("Referring pages.txt", "w+", encoding='utf-8') as f:
    for person, referringpagelist in peopleReferences.items():
        f.write("**"+person+"\n")
        for pagename in referringpagelist:
            f.write("  "+pagename+"\n")

# ...
# Now a list of redirects.
# We use basically the same format:
#   **<target page>
#   <redirect to it>
#   <redirect to it>
# ...
# Now dump the inverse redirects to a file
Log("Writing: Redirects.txt")
with open("Redirects.txt", "w+", encoding='utf-8') as f:
    for redirect, pages in inverseRedirects.items():
        f.write("**"+redirect+"\n")
        for page in pages:
            f.write("      ⭦ "+page+"\n")

# Next, a list of redirects with a missing target
Log("Writing: Redirects with missing target.txt")
allFancy3Pagenames=set([WindowsFilenameToWikiPagename(n) for n in allFancy3PagesFnames])
with open("Redirects with missing target.txt", "w+", encoding='utf-8') as f:
    for key in redirects.keys():
        dest=WikiExtractLink(redirects[key])
        if dest not in allFancy3Pagenames:
            f.write(key+" --> "+dest+"\n")


# ...
# Create and write out a file of peoples' names. They are taken from the titles of pages marked as fan or pro

# Ambiguous names will often end with something in parenthesis which need to be removed for this particular file
def RemoveTrailingParens(s: str) -> str:
    return re.sub("\s\(.*\)$", "", s)       # Delete any trailing ()


# Some names are not worth adding to the list of people names.  Try to detect them.
def IsInterestingName(p: str) -> bool:
    if " " not in p and "-" in p:   # We want to ignore names like "Bob-Tucker" in favor of "Bob Tucker"
        return False
    if " " in p:                    # If there are spaces in the name, at least one of them needs to be followed by a UC letter
        if re.search(" ([A-Z]|de|ha|von|Č)", p) is None:  # We want to ignore "Bob tucker"
            return False
    return True

Log("Writing: Peoples names.txt")
peopleNames=set()
# First make a list of all the pages labelled as "fan" or "pro"
with open("Peoples rejected names.txt", "w+", encoding='utf-8') as f:
    for fancyPage in fancyPagesDictByWikiname.values():
        if fancyPage.IsPerson():
            peopleNames.add(RemoveTrailingParens(fancyPage.Name))
            # Then all the redirects to one of those pages.
            if fancyPage.Name in inverseRedirects.keys():
                for p in inverseRedirects[fancyPage.Name]:
                    if p in fancyPagesDictByWikiname.keys():
                        peopleNames.add(RemoveTrailingParens(fancyPagesDictByWikiname[p].UltimateRedirect))
                        if IsInterestingName(p):
                            peopleNames.add(p)
                        else:
                            f.write("Uninteresting: "+p+"\n")
                    else:
                        Log("Generating Peoples names.txt: "+p+" is not in fancyPagesDictByWikiname")
            else:
                f.write(fancyPage.Name+" Not in inverseRedirects.keys()\n")


with open("Peoples names.txt", "w+", encoding='utf-8') as f:
    peopleNames=list(peopleNames)   # Turn it into a list so we can sort it.
    peopleNames.sort(key=lambda p: p.split()[-1][0].upper()+p.split()[-1][1:]+","+" ".join(p.split()[0:-1]))    # Invert so that last name is first and make initial letter UC.
    for name in peopleNames:
        f.write(name+"\n")
i=0


