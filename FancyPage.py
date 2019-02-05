# A file to define a class to hold the characteristics of a Fancy 3 page
from dataclasses import dataclass, field
import Reference

@dataclass(order=False)
class FancyPage:
    CanName: str=None       # The page's Wikidot canonical name
    Title:  str=None        # The page's title
    Tags:   list=None       # A list of tags associated with this page
    References: list=None   # A list of all the references on this page
    Redirect: str=None      # If this is a redirect page, the name of the page to which it redirects

    def __init__(self, CanName=None, Title=None, Tags=None, References=None, Redirect=None):
        self.CanName=CanName
        self.Title=Title
        self.Tags=Tags
        self.References=References
        self.Redirect=Redirect

    def __hash__(self):
        return self.CanName.__hash__()+self.Title.__hash__()+self.Redirect.__hash__()+self.Tags.__hash__()+self.References.__hash__()

    def __eq__(self, rhs):
        if self.CanName != rhs.CanName:
            return False
        if self.Title != rhs.Title:
            return False
        if self.Tags != rhs.Tags:
            return False
        if self.References != rhs.References:
            return False
        if self.Redirect != rhs.Redirect:
            return False
        return True