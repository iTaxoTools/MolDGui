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
    List = 'From list'
    No = 'None'

    def __str__(self):
        return self.value


class PairwiseSelectMode(Enum):
    All = 'All pairs'
    List = 'From list'
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


class ScoringThreshold(str, Enum):
    Lousy = 'lousy', 'Lousy (66)'
    Moderate = 'moderate', 'Moderate (75)'
    Stringent = 'stringent', 'Stringent (90)'
    VeryStringent = 'very_stringent', 'Very Stringent (95)'

    def __new__(cls, code, label):
        obj = str.__new__(cls, code)
        obj._value_ = code
        obj.label = label
        return obj


class PropertyEnum(Enum):
    def __init__(self, config, key, default, label, description):
        self.config = config  # configuration file key (uppercase)
        self.key = key  # model key
        self.default = default  # model value
        self.label = label  # for Gui
        self.description = description  # for Gui

    def __repr__(self):
        return f'<{self.__class__.__name__}.{self._name_}>'


class AdvancedMDNCProperties(PropertyEnum):
    Cutoff = 'CUTOFF', 'cutoff', '100', 'Cutoff', 'number of informative sites to be considered'
    Nucleotides = 'NUMBERN', 'nucleotides', 5, 'NumberN', 'number of ambiguously called nucleotides allowed',
    Iterations = 'NUMBER_OF_ITERATIONS', 'iterations', 10000, 'Iterations', 'number of iterations of MolD'
    MaxLen1 = 'MAXLEN1', 'max_length_raw', 12, 'MaxLen1', 'maximum length of draft DNCs'
    MaxLen2 = 'MAXLEN2', 'max_length_refined', 7, 'MaxLen2', 'maximum length of refined mDNCs'
    Iref = 'IREF', 'indexing_reference', 'NO', 'Iref', 'indexing reference sequence'


class AdvancedRDNSProperties(PropertyEnum):
    Pdiff = 'PDIFF', 'p_diff', None, 'Pdiff', 'percent difference between original and modified sequences',
    NmaxSeq = 'NMAXSEQ', 'n_max', 5, 'NmaxSeq', 'maximum number of sequences per taxon to modify',
    Scoring = 'SCORING', 'scoring', ScoringThreshold.Moderate, 'Scoring', 'determines the scoring threshold out of 100 tests',


class MoldResults(NamedTuple):
    diagnosis: Path | None
    pairwise: Path | None
