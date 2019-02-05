

#------------------------------------------------------------------
# Take a raw name (mixed case, special characters, a potential category, etc.) and turn it into a properly formatted cannonicized name:
#       Either "<category>:<name>" or, when there is no category, just "<name>"
#       In both cases, the <> text is cannonicized
def Cannonicize(pageNameZip):
    if pageNameZip is None:
        return None
    pageName = pageNameZip.lower()

    # Split out the category, if any.
    splitName=pageName.split(":")
    if len(splitName) > 2:
        splitName=[splitName[0], " ".join(splitName[1:])]  # Assume first colon is the category divider.  The rest will eventually be ignored

    # Handle the case of no category
    if len(splitName) == 1:
        canName=CannonicizeString(splitName[0])
        name=splitName[0]
    else:
        canName=CannonicizeString(splitName[0])+":"+CannonicizeString(splitName[1])
        name=splitName[0]+":"+splitName[1]

    return canName