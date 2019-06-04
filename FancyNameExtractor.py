import os
import re as RegEx
import xml.etree.ElementTree as ET
import Reference
import FancyPage
import Helpers

# The goal of this program is to produce an index to all of the names on Fancy 3 and fanac.org with links to everything interesting about them.
# We'll construct a master list of names with a preferred name and zero or more variants.
# This master list will be derived from Fancy with additions from fanac.org
# The list of interesting links will include all links in Fancy 3, and all non-housekeeping links in fanac.org
#   A housekeeping link is one where someone is credited as a photographer or having done scanning or the like
# The links will be sorted by importance
#   This may be no more than putting the Fancy 3 article first, links to fanzines they edited next, and everything else after that

# The strategy is to start with Fancy 3 and get that working, then bring in fanac.org.

# We'll work entirely on the local copies of the two sites.

# There will be a dictionary, nameVariants, indexed by every form of every name. The value will be the canonical form of the name.
# There will be a second dictionary, people, indexed by the canonical name and containing an unordered list of Reference structures
# A Reference will contain:
#       The canonical name
#       The as-used name
#       An importance code (initially 1, 2 or 3 with 3 being least important)
#       If a reference to Fancy, the name of the page (else None)
#       If a reference to fanac.org, the URL of the relevant page (else None)
#       If a redirect, the redirect name

nameVariants={}
peopleReferences={}

#Test

# ----------------------------------------------------------
# Read a page's tags and title
def ReadTagsAndTitle(pagePath: str):
    tree=ET.ElementTree().parse(os.path.splitext(pagePath)[0]+".xml")

    titleEl=tree.find("title")
    if titleEl is None:
        title=None
    else:
        title=titleEl.text

    tags=[]
    tagsEl=tree.find("tags")
    if tagsEl is not None:
        tagElList=tagsEl.findall("tag")
        if len(tagElList) != 0:
            for el in tagElList:
                tags.append(el.text)
    return tags, title


#*******************************************************
# Is this page a redirect?  If so, return the page it redirects to.
def IsRedirect(pageText: str):
    pageText=pageText.strip()  # Remove leading and trailing whitespace
    if pageText.lower().startswith('[[module redirect destination="') and pageText.endswith('"]]'):
        return pageText[31:].rstrip('"]')
    return None


#*******************************************************
# Read a page and return a FancyPage
# pagePath will be the path to the page's source (i.e., ending in .txt)
def DigestPage(path: str, page: str):
    pagePath=os.path.join(path, page)+".txt"

    if not os.path.isfile(pagePath):
        #log.Write()
        return None

    fp=FancyPage.FancyPage()
    fp.CanonName=os.path.splitext(page)[0]     # Page is name+".txt", with no path.  Get rid of the extension and save the name.
    fp.Tags, fp.Title=ReadTagsAndTitle(pagePath)

    # Load the page's source
    with open(os.path.join(pagePath), "rb") as f:   # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
        source=f.read().decode("cp437") # decode("cp437") is magic to handle funny foreign characters

    # If the page is a redirect, we're done.
    redirect=IsRedirect(source)
    if redirect is not None:
        fp.Redirect=redirect
        return fp

    # Now we scan the source for links.
    # A link is one of these formats:
    #   [[[link]]]
    #   [[[link|display text]]]
    links=set()     # Start out with a set so we don't keep duplicates
    while len(source) > 0:
        loc=source.find("[[[")
        if loc == -1:
            break
        loc2=source.find("]]]", loc)
        if loc2 == -1:
            break
        link=source[loc+3:loc2]
        # Now look at the possibility of the link containing display text.  If there is a "|" in the link, then only the text to the left of the "|" is the link
        if "|" in link:
            link=link[:link.find("|")]

        links.add(Reference.Reference(LinkText=link.strip(), ParentPageName=page, CanonName=Helpers.CanonicizeString(link.strip())))

        # trim off the text which has been processed and try again
        source=source[loc2+3:]

    fp.OutgoingReferences=list(links)       # We need to turn the set into a list

    return fp


fancySitePath=r"C:\Users\mlo\Documents\usr\Fancyclopedia\Python\site"

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folder named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
print("***Creating a list of all Fancyclopedia pages")
allFancy3PagesCanon = [f[:-4] for f in os.listdir(fancySitePath) if os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]
#allFancy3PagesCanon= [f for f in allFancy3PagesCanon if f[0] in "ab"]        # Just to cut down the number of pages for debugging purposes

fancyPagesReferences={}
fancyCanonNameToTitle={}

print("***Scanning Fancyclopedia pages for links")
for pageCanName in allFancy3PagesCanon:
    if pageCanName.startswith("index_"):  # Don't look at the index_ pages
        continue
    val=DigestPage(fancySitePath, pageCanName)
    if val is not None:
        fancyCanonNameToTitle[val.CanonName]=val.Title
        fancyPagesReferences[pageCanName]=val

with open("Canonical names to real names.txt", "w+", encoding='utf8') as f:
    for canon, title in fancyCanonNameToTitle.items():
        if not canon.startswith("system_"):
            f.write(canon+"-->"+title+"\n")


print("***Computing redirect structure")
# A FancyPage has an UltimateRedirect which can only be filled in once all the redirects are known.
# Run through the pages and fill in UltimateRedirect.
def GetUltimateRedirect(fancyPagesReferences, redirect):
    if redirect is None:
        return None
    canredirect=Helpers.CanonicizeString(redirect)
    if canredirect not in fancyPagesReferences.keys():  # Target of redirect does not exist, so this redirect is the ultimate redirect
        return redirect
    if fancyPagesReferences[canredirect] is None:       # Target of redirect does not exist, so this redirect is the ultimate redirect
        return redirect
    if fancyPagesReferences[canredirect].Redirect is None: # Target is a real page, so that real page is the ultimate redirect
        return fancyPagesReferences[canredirect].Title #TODO: Confirm that title is actually what we want here...
    return GetUltimateRedirect(fancyPagesReferences, fancyPagesReferences[canredirect].Redirect)

# Fill in the UltimateRedirect element
for canname, fancyPage in fancyPagesReferences.items():
    if fancyPage.Redirect is not None:
        fancyPage.UltimateRedirect=GetUltimateRedirect(fancyPagesReferences, fancyPage.Redirect)

# OK, now we have a dictionary of all the pages on Fancy 3, which contains all of their outgoing links
# Build up a dictionary of redirects.  It is indexed by the canonical name of a page and the value is the canonical name of the ultimate redirect
# Build up an inverse list of all the pages that redirect *to* a given page, also indexed by the page's canonical name. The value here is a list of canonical names.
redirects={}
inverseRedirects={}
for canname, fancyPage in fancyPagesReferences.items():
    if fancyPage.Redirect is not None:
        if fancyPage.Redirect is not None:
            assert fancyPage.UltimateRedirect is not None
        else:
            assert fancyPage.UltimateRedirect is None
        redirects[fancyPage.CanonName]=fancyPage.UltimateRedirect
        if fancyPage.Redirect not in inverseRedirects.keys():
            inverseRedirects[fancyPage.Redirect]=[]
        inverseRedirects[fancyPage.Redirect].append(fancyPage.CanonName)
        if fancyPage.UltimateRedirect not in inverseRedirects.keys():
            inverseRedirects[fancyPage.UltimateRedirect]=[]
        if fancyPage.UltimateRedirect != fancyPage.Redirect:
            inverseRedirects[fancyPage.UltimateRedirect].append(fancyPage.CanonName)

# Create a dictionary of page references for people pages.
# The key is a page's canonical name; the value is a list of pages at which they are referenced.

# First locate all the people and create empty entries for them
peopleReferences={}
print("***Creating list of people references")
for canpagename, fancyPage in fancyPagesReferences.items():
    if fancyPage.IsPerson():
        if canpagename not in peopleReferences.keys():
            peopleReferences[canpagename]=[]

# Now go through all outgoing references on the pages and add those which reference a person to that person's list
for canpagename, fancyPage in fancyPagesReferences.items():
    if fancyPage.OutgoingReferences is not None:
        for outRef in fancyPage.OutgoingReferences:
            cannonLink=Helpers.Canonicize(outRef.LinkText)
            if cannonLink in peopleReferences.keys():    # So it's a people
                peopleReferences[cannonLink].append(canpagename)

print("***Writing reports")
# Write out a file containing canonical names, each with a list of pages which refer to it.
# The format will be
#     **<canonical name>
#     <referring page>
#     <referring page>
#     ...
#     **<cannonical name>
#     ...
with open("Referring pages.txt", "w+") as f:
    for cannonPerson, pagenames in peopleReferences.items():
        f.write("**"+fancyCanonNameToTitle[cannonPerson]+"\n")
        for pagename in pagenames:
            f.write("  "+pagename+"\n")

# Now a list of redirects.
# We use basically the same format:
#   **<target page>
#   <redirect to it>
#   <redirect to it>
# ...
# Now dump the inverse redirects to a file
with open("Redirects.txt", "w+", encoding='utf-8') as f:
    for redirect, pages in inverseRedirects.items():
        f.write("**"+redirect+"\n")
        for page in pages:
            f.write("  "+page+"\n")

# Create and write out a file of peoples' names. They are taken from the titles of pages marked as fan or pro
peopleNames=[]
# First make a list of all the pages labelled as "fan" or "pro"
for canpagename, fancyPage in fancyPagesReferences.items():
    if fancyPage.IsPerson():
        peopleNames.append(fancyPage.Title)
        # Then all the redirects to one of those pages.
        pagename=fancyCanonNameToTitle[canpagename]
        if pagename in inverseRedirects.keys():
            for p in inverseRedirects[pagename]:
                peopleNames.append(fancyCanonNameToTitle[p])

# De-dupe it
peopleNames=list(set(peopleNames))

# Sort it by the number of tokens in the name
peopleNames.sort(key=lambda n: len(n.split()), reverse=True)

with open("Peoples names.txt", "w+") as f:
    # First all the pages labelled as "fan" or "pro"
    for name in peopleNames:
        f.write(name+"\n")
i=0


