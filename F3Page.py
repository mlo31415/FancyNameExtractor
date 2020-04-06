# A file to define a class to hold the characteristics of a Fancy 3 page
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from Reference import Reference

@dataclass(order=False)
class F3Page:
    def __init__(self, WikiFilename: Optional[str]=None,
                 DisplayTitle: Optional[str]=None,
                 Name: Optional[str]=None,
                 Tags: Optional[List[str]]=None,
                 Redirect: Optional[str]=None,
                 UltimateRedirect: Optional[str]=None,
                 OutgoingReferences: List[Reference]=None
                 ):
        self._WikiFilename=WikiFilename         # The page's Mediawiki "file" name, e.g., Now_Is_the_Time
        self._DisplayTitle=DisplayTitle         # The title displayed for the page (takes DISPLAYTITLE into account if it has been set; otherwise is Name)
        self._Name=Name                         # The page's Mediawiki name (ignores DISPLAYTITLE, so if DISPLAYTITLE is absent is the same as DisplayTitle)  e.g., Now Is the Time
        self._Redirect=Redirect                 # If this is a redirect page, the Wikiname name of the page to which it redirects
        self._UltimateRedirect=UltimateRedirect         # If this is a redirect page, the non-canonical name of the ultimate page that this chain of redirects leads to
        self._Tags=Tags                         # A list of tags associated with this page
        self._OutgoingReferences=OutgoingReferences     # A list of all the references on this page

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
        return self._WikiFilename
    @WikiUrlname.setter
    def WikiUrlname(self, val: Optional[str]):
        self._WikiFilename=val

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
    def UltimateRedirect(self) -> str:
        return self._UltimateRedirect
    @UltimateRedirect.setter
    def UltimateRedirect(self, val: Optional[str]):
        self._UltimateRedirect=val

    @property
    def Tags(self) -> List[str]:
        return self._Tags
    @Tags.setter
    def Tags(self, val: List[str]):
        self._Tags=val

    @property
    def OutgoingReferences(self) -> List[Reference]:
        return self._OutgoingReferences
    @OutgoingReferences.setter
    def OutgoingReferences(self, val: Optional[str]):
        self._OutgoingReferences=val