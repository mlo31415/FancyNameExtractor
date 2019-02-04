# A file to define the Reference class
from dataclasses import dataclass, field

#
#


@dataclass(order=False)
class Reference:
    CanName: str=None       # The Wikidot canonical name
    UsedName: str=None      # The as-used name (the link text in Wikidot)
    Importance: int=None    # An importance code (initially 1, 2 or 3 with 3 being least important)
    PageName: str=None      # If from a reference to Fancy, the name of the Fancy page it is on (else None)
    FanacURL: str=None      # If a reference to fanac.org, the URL of the page it was on (else None)
    RedirectName: str=None  # If a redirect, the redirect's target.  Note that not all redirects are from Fancy


