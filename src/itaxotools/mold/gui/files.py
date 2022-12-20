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

"""File checking and parsing"""

from pathlib import Path

from .types import TaxonRank, GapsAsCharacters, ScoringThreshold


def is_fasta(path):
    with open(path) as file:
        char = file.read(1)
        return char == '>'

def check_sequence_file(path):
    error_caption = 'Error opening sequence file: \n'

    with open(path) as file:
        char = file.read(1)
        if char != '>':
            raise Exception(error_caption + 'Sequences must be provided in the Fasta format, and the file must begin with the ">" symbol.')

        line = file.readline()
        split = line.split('|')
        if len(split) < 2:
            raise Exception(error_caption + 'Taxon identifiers must be provided after each sequence identifier, separated by a single pipe symbol: "|"')
        elif len(split) > 2:
            raise Exception(error_caption + 'Each identifier line must only contain a single pipe symbol: "|"')


def parse_configuration_file(path):
    error_caption = 'Error opening configuration file: \n'

    reference = {
        'QTAXA': lambda x: x,
        'INPUT_FILE': lambda x: Path(x),
        'TAXON_RANK': lambda x: TaxonRank(x),
        'GAPS_AS_CHARS': lambda x: GapsAsCharacters(x.lower()),
        'CUTOFF': lambda x: x if x != '' else None,
        'NUMBERN': lambda x: int(x) if x != '' else None,
        'NUMBER_OF_ITERATIONS': lambda x: int(x) if x != '' else None,
        'MAXLEN1': lambda x: int(x) if x != '' else None,
        'MAXLEN2': lambda x: int(x) if x != '' else None,
        'IREF': lambda x: x if x != '' else None,
        'PDIFF': lambda x: int(x) if x != '' else None,
        'NMAXSEQ': lambda x: int(x) if x != '' else None,
        'SCORING': lambda x: ScoringThreshold(x) if x != '' else None,
        'OUTPUT_FILE': None,
        'ORIG_FNAME': None,
    }

    params = {}
    with open(path) as file:
        for line in file:
            line = line.strip()
            if line.startswith('#'):
                continue
            split = line.split('=')
            if len(split) == 2 and len(split[1]) != 0:
                params[split[0]] = split[1].replace(' ', '')

    if not params:
        raise Exception(error_caption + f'No parameters found in file: {str(path)}')

    for param in params:
        if not param.upper() in reference.keys():
            raise Exception(error_caption + f'Invalid parameter name: {param}')

    return {k.upper(): reference[k.upper()](v) for k, v in params.items() if reference[k.upper()] is not None}
