from dataclasses import dataclass


@dataclass
class ResolutionProfile:

    name: str

    width: int

    height: int

    aspect: str


RESOLUTION_PROFILES = {

    "Square":
        ResolutionProfile(
            "Square",
            1024,
            1024,
            "1:1"
        ),

    "Portrait":
        ResolutionProfile(
            "Portrait",
            1024,
            1536,
            "2:3"
        ),

    "Landscape":
        ResolutionProfile(
            "Landscape",
            1536,
            1024,
            "3:2"
        ),

    "YouTube 1080p":
        ResolutionProfile(
            "YouTube 1080p",
            1920,
            1080,
            "16:9"
        ),

    "YouTube 4K":
        ResolutionProfile(
            "YouTube 4K",
            3840,
            2160,
            "16:9"
        ),

    "TikTok":
        ResolutionProfile(
            "TikTok",
            1080,
            1920,
            "9:16"
        ),

    "Instagram Reel":
        ResolutionProfile(
            "Instagram Reel",
            1080,
            1920,
            "9:16"
        ),
}