# A file to define a class to hold the characteristics of a Fancy 3 page
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List, Union

from F3Reference import F3Reference

from Log import Log
from HelpersPackage import IsInt

@dataclass(order=False)
class F3Page:
    def __init__(self):
        self._WikiFilename: Optional[str]=None                      # The page's Mediawiki "file" name, e.g., Now_Is_the_Time
        self._DisplayTitle: Optional[str]=None                      # The title displayed for the page (takes DISPLAYTITLE into account if it has been set; otherwise is Name)
        self._Name: Optional[str]=None                              # The page's Mediawiki name (ignores DISPLAYTITLE, so if DISPLAYTITLE is absent is the same as DisplayTitle)  e.g., Now Is the Time
        self._Redirect: Optional[str]=None                          # If this is a redirect page, the Wikiname name of the page to which it redirects
        self._UltimateRedirect: Optional[bool]=None                  # If this is a redirect page, the non-canonical name of the ultimate page that this chain of redirects leads to
        self._IsRedirectpage: Optional[str]=None
        self._Tags: Optional[List[str]]=None                        # A list of tags associated with this page
        self._OutgoingReferences: Optional[List[F3Reference]]=None    # A list of all the references on this page
        self._WikiUrlname: Optional[str]=None
        self._NumRevisions: Optional[int]=None
        self._Pageid: Optional[str]=None
        self._Revid: Optional[str]=None
        self._Edittime: Optional[str]=None
        self._Permalink: Optional[str]=None
        self._Timestamp: Optional[str]=None
        self._User: Optional[str]=None
        self._WindowsFilename: Optional[str]=None
        self._Categories: Optional[str]=None

    def __hash__(self):
        return self._WikiFilename.__hash__()+self._DisplayTitle.__hash__()+self._Name.__hash__()+self._Redirect.__hash__()+self._UltimateRedirect.__hash__()+self._Tags.__hash__()+self._OutgoingReferences.__hash__()

    def __eq__(self, rhs: F3Page):
        if self._WikiFilename != rhs._WikiFilename:
            return False
        if self._DisplayTitle != rhs._DisplayTitle:
            return False
        if self._Name != rhs._Name:
            return False
        if self._Redirect != rhs._Redirect:
            return False
        if self._UltimateRedirect != rhs._UltimateRedirect:
            return False
        if self._Tags != rhs._Tags:
            return False
        if self._OutgoingReferences != rhs._OutgoingReferences:
            return False
        return True

    def IsPerson(self) -> bool:
        return self._Tags is not None and ("fan" in self._Tags or "pro" in self._Tags)

    @property
    def DisplayTitle(self) -> str:
        if self._DisplayTitle is not None:
            return self._DisplayTitle
        return self._Name
    @DisplayTitle.setter
    def DisplayTitle(self, val: Optional[str]):
        self._DisplayTitle=val

    @property
    def WikiUrlname(self) -> str:
        return self._WikiUrlname
    @WikiUrlname.setter
    def WikiUrlname(self, val: Optional[str]):
        self._WikiUrlname=val

    @property
    def Name(self) -> str:
        return self._Name
    @Name.setter
    def Name(self, val: Optional[str]):
        self._Name=val

    @property
    def Redirect(self) -> str:
        return self._Redirect
    @Redirect.setter
    def Redirect(self, val: Optional[str]):
        self._Redirect=val

    @property
    def UltimateRedirect(self) -> Optional[str]:
        return self._UltimateRedirect
    @UltimateRedirect.setter
    def UltimateRedirect(self, val: str):
        self._UltimateRedirect=val

    @property
    def IsRedirectpage(self) -> Optional[bool]:
        return self._IsRedirectpage
    @IsRedirectpage.setter
    def IsRedirectpage(self, val: str):
        self._IsRedirectpage=(val == "True")

    @property
    def Tags(self) -> List[str]:
        return self._Tags
    @Tags.setter
    def Tags(self, val: List[str]):
        self._Tags=val

    @property
    def OutgoingReferences(self) -> List[F3Reference]:
        return self._OutgoingReferences
    @OutgoingReferences.setter
    def OutgoingReferences(self, val: Optional[str]):
        self._OutgoingReferences=val

    @property
    def WikiFilename(self) -> Optional[str]:
        return self._WikiFilename
    @WikiFilename.setter
    def WikiFilename(self, val: Optional[str]):
        self._WikiFilename=val

    @property
    def NumRevisions(self) -> Optional[int]:
        return self._NumRevisions
    @NumRevisions.setter
    def NumRevisions(self, val: Union[str, int]):
        if isinstance(val, int):
            self._NumRevisions=val
        elif isinstance(val, str):
            if IsInt(val):
                self._NumRevisions=int(val)
            else:
                Log("F3Page.NumRevisions setter: not an int: '"+val+"'", isError=True)
        else:
            self._NumRevisions=None

    @property
    def Pageid(self) -> Optional[int]:
        return self._Pageid
    @Pageid.setter
    def Pageid(self, val: Union[str, int]):
        if isinstance(val, int):
            self._Pageid=val
        elif isinstance(val, str):
            if IsInt(val):
                self._Pageid=int(val)
            else:
                Log("F3Page.Pageid setter: not an int: '"+val+"'", isError=True)
        else:
            self._Pageid=None

    @property
    def Revid(self) -> Optional[int]:
        return self._Revid
    @Revid.setter
    def Revid(self, val: Union[str, int]):
        if isinstance(val, int):
            self._Revid=val
        elif isinstance(val, str):
            if IsInt(val):
                self._Revid=int(val)
            else:
                Log("F3Page.Revid setter: not an int: '"+val+"'", isError=True)
        else:
            self._Revid=None

    @property
    def Edittime(self) -> Optional[str]:
        return self._Edittime
    @Edittime.setter
    def Edittime(self, val: Optional[str]):
        self._Edittime=val

    @property
    def Permalink(self) -> Optional[str]:
        return self._Permalink
    @Permalink.setter
    def Permalink(self, val: Optional[str]):
        self._Permalink=val

    @property
    def Timestamp(self) -> Optional[str]:
        return self._Timestamp
    @Timestamp.setter
    def Timestamp(self, val: Optional[str]):
        self._Timestamp=val

    @property
    def User(self) -> Optional[str]:
        return self._User
    @User.setter
    def User(self, val: Optional[str]):
        self._User=val

    @property
    def WindowsFilename(self) -> Optional[str]:
        return self._WindowsFilename
    @WindowsFilename.setter
    def WindowsFilename(self, val: Optional[str]):
        self._WindowsFilename=val

    @property
    def Categories(self) -> Optional[str]:
        return self._Categories
    @Categories.setter
    def Categories(self, val: Optional[str]):
        self._Categories=val
