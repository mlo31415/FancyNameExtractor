import os
import re as RegEx
import xml.etree.ElementTree as ET
import Reference
import FancyPage

# The goal of this program is to produce an index to all of the names on Fancy 3 and fanac.org with links to everything interesting about them.
# We'll construct a master list of names with a preferred name and zero or more variants.
# This master list will be derived from Fancy with additions from fanac.org
# The list of interesting links will include all links in Fancy 3, and all non-housekeeping links in fanac.org
#   A housekeeping link is one where someone is credited as a photographer or having done scanning or the like
# The links will be sorted by importance
#   This may be no more than putting the Fancy 3 article first, links to fanzines they edited next, and everything else after that

# The strategy is to start with Fancy 3 and get that working, then bring in fanac.org.

# We'll work entirely on the local copies of the two sites.

# There will be a dictionary, nameVariants, indexed by every form of every name. The value will be the cannonical form of the name.
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
def ReadTagsAndTitle(pagePath):
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
# Read a page and return a FancyPage
# pagePath will be the path to the page's source (i.e., ending in .txt)
def ReadPage(path, page):
    pagePath=os.path.join(path, page)+".txt"

    if not os.path.isfile(pagePath):
        #log.Write()
        return None

    fancyPage=FancyPage.FancyPage()
    fancyPage.CanName=os.path.splitext(page)[0]     # Page is name+".txt", no path.  Get rid of the extension and save the name.

    tags, title=ReadTagsAndTitle(pagePath)
    fancyPage.Tags=tags
    fancyPage.Title=title

    # Read through the source pulling out links.
    with open(os.path.join(pagePath), "rb") as f:   # Reading in binary and doing the funny decode is to handle special characters embedded in some sources.
        source=f.read().decode("cp437")

    def IsRedirect(pageText):
        pageText=pageText.strip()  # Remove leading and trailing whitespace
        if pageText.lower().startswith('[[module redirect destination="') and pageText.endswith('"]]'):
            return pageText[31:].rstrip('"]')
        return None

    # If this is a redirect, we're done.
    redirect=IsRedirect(source)
    if redirect:
        fancyPage.Redirect=redirect
        return fancyPage

    # Now we scan the source for links.
    # A link is one of these formats:
    #   [[[link]]]
    #   [[[link|display text]]]
    links=[]
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

        ref=Reference.Reference(LinkText=link.strip(), ParentPageName=page)
        links.append(ref)

        # trim off the text which has been processed and try again
        source=source[loc2:]

    fancyPage.References=links

    return fancyPage


#*******************************************************
# Is this likely to be a person's name?
# A hit is of the form <name1> <initial> <name2> where name1 is in the list of first names
def IsAName(name):
    pattern="^([A-Z]([a-z]|+\.)\s+([A-Z]\.?)\s+([A-Z]([a-z]|+\.)$"
    m=RegEx.match(pattern, name.strip())
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
print("***Creating list of all pages")
allFancy3Pages = [f[:-4] for f in os.listdir(fancySitePath) if f[0] == "a" and os.path.isfile(os.path.join(fancySitePath, f)) and f[-4:] == ".txt"]

fancyPagesReferences={}

print("***Scanning pages for links")
for pageCanName in allFancy3Pages:
    fancyPagesReferences[pageCanName]=ReadPage(fancySitePath, pageCanName)


i=0


