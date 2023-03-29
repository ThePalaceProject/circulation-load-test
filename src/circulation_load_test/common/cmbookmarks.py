import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional


class CMBookmarkElement(ABC):
    @abstractmethod
    def to_json_dict(self) -> Mapping[str, Any]:
        pass


class CMLocator(CMBookmarkElement):
    """The base locator type."""


@dataclass
class CMLocatorLegacyCFI(CMLocator):
    id_ref: Optional[str]
    cfi: Optional[str]
    progression: Optional[float]

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "@type": "LocatorLegacyCFI",
            "idref": self.id_ref,
            "contentCFI": self.cfi,
            "progressWithinChapter": self.progression,
        }


@dataclass
class CMLocatorHrefProgression(CMLocator):
    href: str
    progression: float

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "@type": "LocatorHrefProgression",
            "idref": self.href,
            "progressWithinChapter": self.progression,
        }


@dataclass
class CMLocatorPage(CMLocator):
    page: int

    def to_json_dict(self) -> Mapping[str, Any]:
        return {"@type": "LocatorPage", "page": self.page}


@dataclass
class CMLocatorAudioBookTime(CMLocator):
    part: int
    chapter: int
    title: str
    duration: int
    time_ms: float
    id: str

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "@type": "LocatorAudioBookTime",
            "part": self.part,
            "chapter": self.chapter,
            "title": self.title,
            "audiobookID": self.id,
            "duration": self.duration,
            "time": self.time_ms,
        }


@dataclass
class CMBookmarkTarget(CMBookmarkElement):
    locator: CMLocator
    source: str

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "selector": {
                "type": "oa:FragmentSelector",
                "value": json.dumps(self.locator.to_json_dict()),
            },
            "source": self.source,
        }


@dataclass
class CMBookmarkBody(CMBookmarkElement):
    device_id: str
    time: str
    others: Mapping[str, str]

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "http://librarysimplified.org/terms/time": self.time,
            "http://librarysimplified.org/terms/device": self.device_id,
        }


class CMMotivation(Enum):
    IDLING = 1
    BOOKMARKING = 2


@dataclass
class CMBookmark(CMBookmarkElement):
    id: str
    target: CMBookmarkTarget
    motivation: CMMotivation
    body: CMBookmarkBody

    def to_json_dict(self) -> Mapping[str, Any]:
        return {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "Annotation",
            "id": self.id,
            "body": self.body.to_json_dict(),
            "motivation": "http://www.w3.org/ns/oa#bookmarking",
            "target": self.target.to_json_dict(),
        }
