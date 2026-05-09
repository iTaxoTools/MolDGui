# MoldGui

[![PyPI - Version](https://img.shields.io/pypi/v/itaxotools-mold-gui?color=tomato)](
    https://pypi.org/project/itaxotools-mold-gui)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/itaxotools-mold-gui)](
    https://pypi.org/project/itaxotools-mold-gui)
[![GitHub - Windows](https://img.shields.io/github/actions/workflow/status/iTaxoTools/MolDGui/windows.yml?label=windows)](
    https://github.com/iTaxoTools/MolDGui/actions/workflows/windows.yml)
[![GitHub - macOS](https://img.shields.io/github/actions/workflow/status/iTaxoTools/MolDGui/macos.yml?label=macos)](
    https://github.com/iTaxoTools/MolDGui/actions/workflows/macos.yml)

Identify diagnostic nucleotide combinations (DNCs) in DNA sequence alignments, which can be used to provide formal diagnoses of these taxa. This is in the form of "redundant DNC” (rDNC), which takes into account unsampled genetic diversity.

This is a Qt GUI for [Mold v1.4.3](https://github.com/SashaFedosov/MolD/tree/9bc74146).

## Executables

Download and run the standalone executables without installing Python.

[![Release](https://img.shields.io/badge/release-MolD_1.4.3-red?style=for-the-badge)](
    https://github.com/iTaxoTools/MolDGui/releases/v1.4.3)
[![Windows](https://img.shields.io/badge/Windows-blue.svg?style=for-the-badge&logo=data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCEtLSBDcmVhdGVkIHdpdGggSW5rc2NhcGUgKGh0dHA6Ly93d3cuaW5rc2NhcGUub3JnLykgLS0+Cjxzdmcgd2lkdGg9IjQ4IiBoZWlnaHQ9IjQ4IiB2ZXJzaW9uPSIxLjEiIHZpZXdCb3g9IjAgMCAxMi43IDEyLjciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CiA8ZyBmaWxsPSIjZmZmIiBzdHJva2UtbGluZWNhcD0ic3F1YXJlIiBzdHJva2Utd2lkdGg9IjMuMTc0OSI+CiAgPHJlY3QgeD0iLjc5MzczIiB5PSIuNzkzNzMiIHdpZHRoPSI1LjAyNyIgaGVpZ2h0PSI1LjAyNyIvPgogIDxyZWN0IHg9IjcuMTQzNiIgeT0iLjc5MzczIiB3aWR0aD0iNC43NjI0IiBoZWlnaHQ9IjUuMDI3Ii8+CiAgPHJlY3QgeD0iLjc5MzczIiB5PSI2Ljg3OSIgd2lkdGg9IjUuMDI3IiBoZWlnaHQ9IjUuMDI3Ii8+CiAgPHJlY3QgeD0iNy4xNDM2IiB5PSI2Ljg3OSIgd2lkdGg9IjQuNzYyNCIgaGVpZ2h0PSI1LjAyNyIvPgogPC9nPgo8L3N2Zz4K)](
    https://github.com/iTaxoTools/MolDGui/releases/download/v1.4.3/MolD-1.4.3-windows-x64.exe)
[![MacOS](https://img.shields.io/badge/macOS-slategray.svg?style=for-the-badge&logo=apple)](
    https://github.com/iTaxoTools/MolDGui/releases/download/v1.4.3/MolD-1.4.3-macos-universal2.dmg)

## Installation

MolD is available on PyPI and can be installed using `pip`:

```
pip install itaxotools-mold-gui
```

After installation, run the program with:

```
mold-gui
```

You may also invoke the command-line version of MolD:
```
mold
```

## Manual
You can read more about MolD and how to use it in the manual.<br>
[MolD_v1_4_manual.pdf](src/itaxotools/mold/gui/docs/MolD_v1_4_manual.pdf)


## Citations

The graphical interface for Mold was developed by S. Patmanidis in the framework of the iTaxoTools project:

<i>Vences, M., A. Miralles, S. Brouillet, J. Ducasse, A. Fedosov, V. Kharchev, I. Kostadinov, S. Kumari, S. Patmanidis, M.D. Scherz, N. Puillandre, S.S. Renner (2021):
iTaxoTools 0.1: Kickstarting a specimen-based software toolkit for taxonomists. - Megataxa 6: 77-92.</i>

Mold was developed by Alexander Fedosov, Guillaume Achaz, Andrey Gontchar, Nicolas Puillandre:

<i>Fedosov A.E., Achaz G., Gontchar A., Puillandre N. 2022. MOLD, a novel software to compile accurate and reliable DNA diagnoses for taxonomic descriptions. Molecular Ecology Resources, 22: 2038-2053. DOI: 10.1111/1755-0998.13590.</i>
