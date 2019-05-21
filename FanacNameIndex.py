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
people={}


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
def ReadPage(path: str, page: str):
    pagePath=os.path.join(path, page)+".txt"

    if not os.path.isfile(pagePath):
        #log.Write()
        return None

    fp=FancyPage.FancyPage()
    fp.CanName=os.path.splitext(page)[0]     # Page is name+".txt", no path.  Get rid of the extension and save the name.

    tags, title=ReadTagsAndTitle(pagePath)
    fp.Tags=tags
    fp.Title=title

    # Read through the source pulling out links.
    with open(os.path.join(pagePath), "rb") as f:   # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
        source=f.read().decode("cp437")

    # If this is a redirect, we're done.
    redirect=IsRedirect(source)
    if redirect is not None:
        fp.Redirect=redirect
        return fp

    # Now we scan the source for links.
    # A link is one of these formats:
    #   [[[link]]]
    #   [[[link|display text]]]
    links=set()
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

        links.add(Reference.Reference(LinkText=link.strip(), ParentPageName=page))

        # trim off the text which has been processed and try again
        source=source[loc2:]

    fp.OutgoingReferences=list(links)

    return fp


#*******************************************************
# Is this likely to be a person's name?
# A hit is of the form <name1> <initial> <name2> where name1 is in the list of first names
def IsAName(s: str):
    pattern="^([A-Z]([a-z]|+\.)\s+([A-Z]\.?)\s+([A-Z]([a-z]|+\.)$"
    m=RegEx.match(pattern, s.strip())
    if m is None:
        return False

    firstnames=["Bob", "Robert", "Don", "Donald", "Alice"]
    if m.groups()[0] in firstnames:
        return True

    return False


fancySitePath=r"C:\Users\mlo\Documents\usr\Fancyclopedia\Python\site"

# The local version of the site is a pair (sometimes also a folder) of files with the Wikidot name of the page.
# <name>.txt is the text of the current version of the page
# <name>.xml is xml containing meta date. The metadata we need is the tags
# If there are attachments, they're in a folder named <name>. We don't need to look at that in this program

# Create a list of the pages on the site by looking for .txt files and dropping the extension
print("***Creating list of all Fancyclopedia pages")
allFancy3Pages = [f[:-4] for f in os.listdir(fancySitePath) if f[0] in "ab" and os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]

fancyPagesReferences={}

print("***Scanning Fancyclopedia pages for links")
for pageCanName in allFancy3Pages:
    val=ReadPage(fancySitePath, pageCanName)
    if val is not None:
        fancyPagesReferences[pageCanName]=val

# OK, now we have a dictionary of all the pages on Fancy 3, which contains all of their outgoing links
# Now build up a dictionary of redirects.  It is indexed by the canonical name of the page and the value is the canonical name of the redirect
redirects={}
for name, fancyPage in fancyPagesReferences.items():
    if fancyPage.Redirect is not None:
        redirects[fancyPage.CanonName]=fancyPage.Redirect

# Some of the redirects are multiple (e.g., A->B->C). Rewrite them to make all redirects single. Re-run this until there are no multiples left
count=1
while count > 0:
    count=0
    for name, redir in redirects.items():
        if redir in redirects.keys():
            redirects[name]=redirects[redirects[name]]
            count+=1
    print("count= "+str(count))

# Create a dictionary of people.  The value is a list of pages at which they are referenced.
# First locate all the people and create empty entries for them
people={}
for name, fancyPage in fancyPagesReferences.items():
    if "fan" in fancyPage.Tags or "pro" in fancyPage.Tags:
        if name not in people.keys():
            people[name]=[]

# Now go through all references of the pages
for name, fancyPage in fancyPagesReferences.items():
    if fancyPage.OutgoingReferences is not None:
        for ref in fancyPage.OutgoingReferences:
            cannonLink=Helpers.Canonicize(ref.LinkText)
            if cannonLink in people.keys():    # So it's a people
                people[cannonLink].append(ref.ParentPageName)


i=0


