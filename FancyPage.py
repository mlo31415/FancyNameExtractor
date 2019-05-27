# A file to define a class to hold the characteristics of a Fancy 3 page
from dataclasses import dataclass

@dataclass(order=False)
class FancyPage:
    CanonName: str=None     # The page's Wikidot canonical name
    Title: str=None         # The page's title
    Redirect: str=None      # If this is a redirect page, the non-canonical name of the page to which it redirects
    UltimateRedirect: str=None      # If this is a redirect page, the non-canonical name of the ultimate page that this chain of redirects leads to
    Tags:   list=None       # A list of tags associated with this page
    OutgoingReferences: list=None   # A list of all the references on this page

    def __init__(self, CanonName=None, Title=None, Tags=None, OutgoingReferences=None, Redirect=None, UltimateRedirect=None):
        self.CanonName=CanonName
        self.Title=Title
        self.Redirect=Redirect
        self.UltimateRedirect=UltimateRedirect
        self.Tags=Tags
        self.OutgoingReferences=OutgoingReferences

    def __hash__(self):
        return self.CanonName.__hash__()+self.Title.__hash__()+self.Redirect.__hash__()+self.UltimateRedirect.__hash__()+self.Tags.__hash__()+self.OutgoingReferences.__hash__()

    def __eq__(self, rhs):
        if self.CanonName != rhs.CanonName:
            return False
        if self.Title != rhs.Title:
            return False
        if self.Redirect != rhs.Redirect:
            return False
        if self.UltimateRedirect != rhs.UltimateRedirect:
            return False
        if self.Tags != rhs.Tags:
            return False
        if self.OutgoingReferences != rhs.References:
            return False
        return True

    def IsPerson(self):
        return self.Tags is not None and ("fan" in self.Tags or "pro" in self.Tags)