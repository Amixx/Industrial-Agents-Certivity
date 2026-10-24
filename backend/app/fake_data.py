"""Canned regulation decisions and updates for the dev-rear-lamp case."""

from typing import NamedTuple

INCLUDED: list[tuple[str, str, str]] = [
    (
        "UN R48",
        "9.3.0",
        "Installation of lighting and light-signalling devices: the rear lamp is a "
        "light-signalling device installed on an M1 vehicle.",
    ),
    (
        "UN R148",
        "1.6.0",
        "Device approval for the rear position, stop and reversing lamp functions the "
        "product combines.",
    ),
    (
        "UN R150",
        "1.2.1",
        "The housing integrates a rear retro-reflector (passive conspicuity), which needs "
        "device approval as a retro-reflective device.",
    ),
    (
        "UN R10",
        "7.2.0",
        "LED modules on a PCB make the lamp an electrical/electronic sub-assembly (ESA), "
        "subject to EMC emission and immunity limits.",
    ),
]

EXCLUDED: list[tuple[str, str]] = [
    ("UN R7", "Position and stop lamps: superseded by the consolidated R148 for new approvals."),
    ("UN R23", "Reversing lamps: superseded by the consolidated R148 for new approvals."),
    ("UN R3", "Retro-reflecting devices: superseded by the consolidated R150 for new approvals."),
    ("UN R6", "Direction indicator: not a function of this product."),
    ("UN R19", "Front fog lamp: not a function of this product."),
    ("UN R38", "Rear fog lamp: not among the functions listed in the spec."),
    ("UN R37", "Filament light sources: the light source is LED modules, no filament bulbs."),
    (
        "UN R128",
        "Replaceable LED light sources only: the LED modules here are non-replaceable and "
        "approved as part of the lamp under R148.",
    ),
    (
        "UN R149",
        "Road illumination devices (headlamps): the rear lamp does not illuminate the road ahead.",
    ),
    ("UN R123", "Adaptive front-lighting systems: front lighting only."),
    (
        "UN R104",
        "Retro-reflective marking tape for heavy vehicles and trailers (M2, M3, N, O): "
        "not M1, and not a marking product.",
    ),
    ("UN R53", "Lighting installation for L3 motorcycles: the target vehicle is M1."),
    ("UN R43", "Safety glazing: the PMMA outer lens is a lamp lens, not vehicle glazing."),
    (
        "UN R26",
        "External projections: assessed on the whole vehicle, not on a component approval.",
    ),
]

PARAGRAPH_COUNTS: dict[str, int] = {"UN R48": 88, "UN R148": 61, "UN R150": 37, "UN R10": 28}


class FakeChange(NamedTuple):
    requirement_id: str | None
    change: str
    new_text: str | None
    reason: str
    page: int
    paragraph: str
    new_id: str | None = None


class FakeUpdate(NamedTuple):
    regulation: str
    from_version: str
    to_version: str
    changes: list[FakeChange]


FAKE_UPDATES: list[FakeUpdate] = [
    FakeUpdate(
        "UN R48",
        "9.3.0",
        "9.4.0",
        [
            FakeChange(
                "G-0057",
                "modified",
                "For all light-signalling devices, including those mounted on the side panels, "
                "the reference axis of the lamp when fitted to the vehicle shall be parallel to "
                "the bearing plane of the vehicle on the road, with a tolerance of ±3° allowed "
                "in each direction; for lamps mounted on movable components this applies in "
                "every fixed position of use.",
                "Supplement clarifies how the alignment tolerance applies to lamps on movable "
                "components such as tailgates.",
                19,
                "5.3",
            ),
            FakeChange(
                "G-0060",
                "modified",
                "For all light-signalling devices, including those mounted on the side panels, "
                "any specific instructions as regards fitting laid down by the manufacturer and "
                "stated in the communication form shall be complied with.",
                "Fitting instructions must now be documented in the type-approval "
                "communication form.",
                19,
                "5.3",
            ),
            FakeChange(
                None,
                "added",
                "Where a stop lamp and a rear position lamp are reciprocally incorporated, the "
                "ratio between their luminous intensities shall be at least 5:1 in the area of "
                "the reference axis.",
                "New paragraph on reciprocally incorporated rear position and stop functions.",
                21,
                "5.11.3",
                "U-R48-01",
            ),
        ],
    ),
    FakeUpdate(
        "UN R148",
        "1.6.0",
        "1.7.0",
        [
            FakeChange(
                "G-0163",
                "modified",
                "The value for ‘a’ shall be at least 4 mm with regard to the size of the "
                "approval marking.",
                "Minimum marking size reduced to suit compact lamp designs.",
                6,
                "3.3.1.2",
            ),
            FakeChange(
                "G-0164",
                "removed",
                None,
                "Sequential-number placement now governed by the Unique Identifier provisions "
                "of the 1958 Agreement.",
                7,
                "3.3.2.2",
            ),
            FakeChange(
                "G-0167",
                "modified",
                "In the case of front or rear position lamps, front or rear end-outline marker "
                "lamps and side-marker lamps, the arrow shall be directed outwards from the "
                "vehicle.",
                "Side-marker lamps added to the arrow-direction rule.",
                7,
                "3.3.2.5.1.1",
            ),
        ],
    ),
    FakeUpdate(
        "UN R10",
        "7.2.0",
        "7.3.0",
        [
            FakeChange(
                "G-0130",
                "modified",
                "When measurements are made using the method described in Annex 7, in the 400 "
                "to 2,500 MHz frequency band the limit shall remain constant at 63 dB "
                "microvolts/m.",
                "Radiated-emission measurement range extended from 1 GHz to 2.5 GHz.",
                10,
                "6.5.2.1",
            ),
            FakeChange(
                None,
                "added",
                "The ESA shall be tested for immunity to transient disturbances conducted along "
                "12 V and 24 V supply lines using the method described in Annex 10.",
                "Conducted transient immunity test made mandatory for all ESAs.",
                11,
                "6.8.1",
                "U-R10-01",
            ),
        ],
    ),
]
