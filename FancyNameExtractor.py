from __future__ import annotations
from typing import Optional, Dict, Set

import os
import re
from collections import namedtuple
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
#       WikiPagename -- the name of the MediaWiki page it was created with and as it appears in a simple Mediawiki link.
#       URLname -- the name of the Mediawiki page in a URL
#                       Basically, spaces are replaced by underscores and the first character is always UC.  #TODO: What about colons? Other special characters?
#       WindowsFilename -- the name of the Windows file in the in the local site: converted using methods in HelperPackage. These names can be derived from the Mediawiki page name and vice-versa.
#       WikiDisplayname -- the display name in MediaWiki: Normally the name of the page, but can be overridden on the page using DISPLAYTITLE
#
#       The URLname and WindowsFilename can be derived from the WikiPagename, but not necessarily vice-versa

#TODO: Revise this

# There will be a dictionary, nameVariants, indexed by every form of every name. The value will be the canonical form of the name.
# There will be a second dictionary, people, indexed by the canonical name and containing an unordered list of Reference structures
# A Reference will contain:
#       The canonical name
#       The as-used name
#       An importance code (initially 1, 2 or 3 with 3 being least important)
#       If a reference to Fancy, the name of the page (else None)
#       If a reference to fanac.org, the URL of the relevant page (else None)
#       If a redirect, the redirect name

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
#allFancy3PagesFnames= [f for f in allFancy3PagesFnames if f[0:2].lower() == "sm"]        # Just to cut down the number of pages for debugging purposes
Log("   "+str(len(allFancy3PagesFnames))+" pages found")

fancyPagesDictByWikiname={}     # Key is page's canname; Val is a FancyPage class containing all the references on the page

Log("***Reading local copies of pages and scanning for links")
for pageFname in allFancy3PagesFnames:
    if pageFname.startswith("Log 202"):     # Ignore Log files in the site directory
        continue
    val=DigestPage(fancySitePath, pageFname)
    if val is not None:
        fancyPagesDictByWikiname[val.Name]=val
    l=len(fancyPagesDictByWikiname)
    if l%1000 == 0:
        if l > 1000:
            Log("--",noNewLine=True)
        if l%20000 == 0:
            Log("")
        Log(str(l), noNewLine=True)
Log("\n   "+str(len(fancyPagesDictByWikiname))+" semi-unique links found")

# A FancyPage has an UltimateRedirect which can only be filled in once all the redirects are known.
# Run through the pages and fill in UltimateRedirect.
def UltimateRedirectName(fancyPagesDictByWikiname: Dict[str, F3Page], redirect: str, recurse: bool=False) -> str:
    global recurselist
    if not recurse:
        recurselist=[]
    if redirect in recurselist:
        Log("Recursion loop: "+str(recurselist))
        return redirect
    recurselist.append(redirect)
    assert redirect is not None
    if redirect not in fancyPagesDictByWikiname.keys():  # Target of redirect does not exist, so this redirect is the ultimate redirect
        return redirect
    if fancyPagesDictByWikiname[redirect] is None:       # Target of redirect does not exist, so this redirect is the ultimate redirect
        return redirect
    if fancyPagesDictByWikiname[redirect].Redirect is None: # Target is a real page, so that real page is the ultimate redirect
        return fancyPagesDictByWikiname[redirect].Name

    return UltimateRedirectName(fancyPagesDictByWikiname, fancyPagesDictByWikiname[redirect].Redirect, recurse=True)

# Fill in the UltimateRedirect element
Log("***Computing redirect structure")
num=0
for fancyPage in fancyPagesDictByWikiname.values():
    if fancyPage.Redirect is not None:
        num+=1
        fancyPage.UltimateRedirect=UltimateRedirectName(fancyPagesDictByWikiname, fancyPage.Redirect)
Log("   "+str(num)+" redirects found", Print=False)


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
class ConDates:
    def __init__(self, Link: str="", Text: str="", DateRange: FanzineDateRange=FanzineDateRange(), Virtual: bool=False):
        self.Link=Link
        self.Text=Text
        self.DateRange=DateRange
        self.Virtual=Virtual



Log("***Beginning scanning for locations")
Log("***Analyzing convention series tables")
# Create a dictionary of convention locations
# The key is the convention name. The value is a set of locations. (There should be only one, of course, but there may be more and we need to understand that so we can fix it)
conventionLocations={}

# First look through the con series pages looking for tables with a location column
# Just collect the data. We'll clean it up later.

def Crosscheck(inputList, checkList):
    ListofHits=[FindIndexOfStringInList(checkList, x) for x in inputList]
    n=next((item for item in ListofHits if item is not None), None)
    return n

# We use a dictionary to eliminate duplicates
# It is keyed by the lower(conventionInstanceName)+conventionInstanceYear
# The value is a ConDates class instance
conventions={}
for page in fancyPagesDictByWikiname.values():
    LogSetHeader("Processing "+page.Name)

    # First, see if this is a Conseries page
    if "Conseries" in page.Tags:
        # We'd like to find the columns containing:
        loccol=None     # The convention's location
        concol=None     # The convention's name
        datecol=None    # The conventions dates
        if page.Table is not None:
            LogSetHeader("Processing conseries "+page.Name)
            listLocationHeaders=["Location"]
            loccol=Crosscheck(listLocationHeaders, page.Table.Headers)
            # We don't log the missing location column because that is common and not an error

            listNameHeaders=["Convention", "Convention Name", "Name"]
            concol=Crosscheck(listNameHeaders, page.Table.Headers)
            if concol is None:
                Log("***Can't find convention column in conseries page "+page.Name, isError=True)

            listDateHeaders=["Date", "Dates"]
            datecol=Crosscheck(listDateHeaders, page.Table.Headers)
            if concol is None:
                Log("***Can't find Date(s)' column in conseries page "+page.Name, isError=True)

            # Walk the convention table
            for row in page.Table.Rows:

                # Look for a "virtual" flag
                virtual=False
                for col in row:
                    if "(virtual)" in col.lower():
                        virtual=True
                        break

                # If the con series table has locations, add the convention and location to the conventionLocations list
                if concol is not None and loccol is not None:
                    if loccol < len(row) and len(row[loccol]) > 0 and concol < len(row) and len(row[concol]) > 0:
                        con=WikiExtractLink(row[concol])
                        if con not in conventionLocations.keys():
                            conventionLocations[con]=set()
                        loc=WikiExtractLink(row[loccol])
                        conventionLocations[con].add(BaseFormOfLocaleName(localeBaseForms,loc))
                        Log("   Conseries: add="+loc+" to "+con)

                # If the conseries has a date, add
                if concol is not None and datecol is not None:
                    if concol < len(row) and len(row[concol]) > 0  and datecol < len(row) and len(row[datecol]) > 0:
                        # Ignore anything in trailing parenthesis
                        p=re.compile("\(.*\)\s?$")
                        datestr=p.sub("", row[datecol])
                        datestr=datestr.replace("&nbsp;", " ").replace("&#8209;", "-")
                        fdr=FanzineDateRange().Match(datestr)
                        if fdr.IsEmpty():
                            Log("***Could not interpret "+row[concol]+"'s date range: "+row[datecol])
                            continue
                        conname=WikiExtractLink(row[concol])
                        if fdr.Duration() > 6:
                            Log("??? "+page.Name+" has long duration: "+str(fdr))
                        conventions[conname.lower()+"$"+str(fdr._startdate.Year)]=ConDates(Link=conname, Text=row[concol], DateRange=fdr, Virtual=virtual)      # We merge conventions with the same name and year

    # Ok, it's not a con series, so see if it's an individual convention page
    # If it's an individual convention page, we search through its text for something that looks like a placename.
    elif "Convention" in page.Tags and "Conseries" not in page.Tags:
        m=ScanForLocales(locales, page.Source)
        if m is not None:
            for place in m:
                place=WikiExtractLink(place)
                if page.Name not in conventionLocations.keys():
                    conventionLocations[page.UltimateRedirect]=set()
                conventionLocations[page.UltimateRedirect].add(BaseFormOfLocaleName(localeBaseForms,place))
                Log("   Convention: add="+page.UltimateRedirect+"  as "+BaseFormOfLocaleName(localeBaseForms,place))
                if page.Name != page.UltimateRedirect:
                    Log("^^^Redirect issue: "+page.Name+" != "+page.UltimateRedirect)


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
connames=[c.Link.replace("[[", "").replace("]]","") for c in conventions]
for conname, conlocs in conventionLocations.items():
    newlocs=set()
    for loc in conlocs:
        if loc in corrections.keys():
            loc=corrections[loc]
        if loc not in connames:
            newlocs.add(loc)
    conventionLocations[conname]=newlocs

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
        conloctext=""
        if conname in conventionLocations.keys():
            cl=conventionLocations[conname]
            if len(cl) > 0:
                for c in cl:
                    if len(conloctext) > 0:
                        conloctext+=", "
                    conloctext+=c
        # And format it for tabular output
        if len(conloctext) > 0:
            conloctext="&nbsp;&nbsp;&nbsp;<small>("+conloctext+")</small>"
        # Format the convention name and location for tabular output
        context=str(con.Text)+conloctext
        if con.DateRange.Cancelled:
            context="<s>"+context+"</s>"
        if con.Virtual:
            context+=" (virtual)"
        # Now write the line
        # We do a year header for each new year, so we need to detect when the current year changes
        if currentYear == con.DateRange._startdate.Year:
            if currentDateRange == con.DateRange:
                f.write("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' ' ||"+context+"\n")
            else:
                f.write(con.DateRange.HTML()+"||"+context+"\n")
                currentDateRange=con.DateRange
        else:
            # When the current date range changes, we put the new date range in the 1st column of the table
            currentYear = con.DateRange._startdate.Year
            currentDateRange=con.DateRange
            f.write('colspan="2"| '+"<big><big>'''"+str(currentYear)+"'''</big></big>\n")
            f.write(str(con.DateRange)+"||"+context+"\n")
    f.write("</tab>")
    f.write("{{conrunning}}\n[[Category:List]]\n")

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


