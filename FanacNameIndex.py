import os
import re as RegEx
import Reference

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

#*******************************************************
# Read a page and return a list of the References on it.
def ReadPageRefs(path, page):
    page=os.path.isfile(os.path.join(path, page))
    if not os.path.exists(page):
        #log.Write()
        return

    # Read the file
    with open(page) as file:
        source=file.readlines()


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
allPages = [f[:-4] for f in os.listdir(fancySitePath) if os.path.isfile(os.path.join(fancySitePath, f)) and os.path.splitext(f)[1] == ".txt"]

for page in allPages:
    listOfRefs=ReadPageRefs(fancySitePath, page)


i=0


