# -----------------------------------------------------------------------------
# MolDGui - Module and Gui for MolD
# Copyright (C) 2022  Patmanidis Stefanos
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from enum import Enum, auto
from typing import NamedTuple
from pathlib import Path


class TaxonSelectMode(Enum):
    All = 'All taxa'
    List = 'From taxon list'
    Line = 'From configuration line'
    No = 'None'

    def __str__(self):
        return self.value


class PairwiseSelectMode(Enum):
    All = 'All pairs'
    List = 'From pair list'
    Line = 'From configuration line'
    No = 'None'

    def __str__(self):
        return self.value


class TaxonRank(str, Enum):
    Species = '1', 'Species:', 'up to 1% divergence from original'
    Supraspecific = '2', 'Supraspecific taxa:', 'up to 5% divergence from original'

    def __new__(cls, code, label, description):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.code = code
        obj.label = label
        obj.description = description
        return obj


class GapsAsCharacters(str, Enum):
    Yes = 'Yes', 'Yes:', 'gaps ("-") are transformed into "D" and treated as independent characters'
    No = 'No', 'No:', 'gaps ("-") are treated as missing data ("N")'

    def __new__(cls, code, label, description):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.code = code
        obj.label = label
        obj.description = description
        return obj


class MoldResults(NamedTuple):
    diagnosis: Path | None
    pairwise: Path | None
