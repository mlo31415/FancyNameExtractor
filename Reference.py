# A file to define the Reference class
from dataclasses import dataclass, field

@dataclass(order=False)
class Reference:
    CanonName: str=None       # The Wikidot canonical name
    LinkText: str=None      # The as-used name (the link text in Wikidot)
    Importance: int=3       # An importance code (initially 1, 2 or 3 with 3 being least important)
    ParentPageName: str=None      # If from a reference to Fancy, the name of the Fancy page it is on (else None)
    FanacURL: str=None      # If a reference to fanac.org, the URL of the page it was on (else None)
    RedirectName: str=None  # If a redirect, the redirect's target.  Note that not all redirects are from Fancy

    def __init__(self, CanonName=None, LinkText=None, Importance=3, ParentPageName=None, FanacURL=None, RedirectName=None):
        self.CanonName=CanonName
        self.LinkText=LinkText
        self.Importance=Importance
        self.ParentPageName=ParentPageName
        self.FanacURL=FanacURL
        self.RedirectName=RedirectName

    def Copy(self, object):
        if type(object) is Reference:
            self.CanonName=object.CanonName
            self.LinkText=object.LinkText
            self.Importance=object.Importance
            self.ParentPageName=object.ParentPageName
            self.FanacURL=object.FanacURL
            self.RedirectName=object.RedirectName
        return self

    def __hash__(self):
        return self.CanonName.__hash__()+self.LinkText.__hash__()+self.Importance.__hash__()+self.ParentPageName.__hash__()+self.FanacURL.__hash__()+self.RedirectName.__hash__()