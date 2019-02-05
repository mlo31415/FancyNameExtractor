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
        self.References=Reference
        self.Redirect=Redirect

