# MoldGui

Identify diagnostic nucleotide combinations (DNCs) in DNA sequence alignments, which can be used to provide formal diagnoses of these taxa. This is in the form of "redundant DNC” (rDNC), which takes into account unsampled genetic diversity.

This is a Qt GUI for [Mold v1.4](https://github.com/SashaFedosov/MolD).


## Windows executable
Download and run the standalone executable without installing Python.<br>
[See the latest release here.](https://github.com/iTaxoTools/MolDGui/releases/latest)


## Manual
You can read more about MolD and how to use it in the manual.<br>
[MolD_v1_4_manual.pdf](src/itaxotools/mold/gui/docs/MolD_v1_4_manual.pdf)


## Installing from source
Clone and install the latest version (requires Python 3.8.6 or later):
```
git clone https://github.com/iTaxoTools/MolDGui.git
cd MolDGui
pip install . -f packages.html
```

To launch the GUI, please use:
```
mold-gui
```

You may also invoke the command-line version of MolD:
```
mold
```

## Packaging

It is recommended to use PyInstaller from within a virtual environment:
```
pip install ".[dev]" -f packages.html
pyinstaller scripts/mold.spec
```


## Citations

The graphical interface for Mold was developed by S. Patmanidis in the framework of the iTaxoTools project:

<i>Vences, M., A. Miralles, S. Brouillet, J. Ducasse, A. Fedosov, V. Kharchev, I. Kostadinov, S. Kumari, S. Patmanidis, M.D. Scherz, N. Puillandre, S.S. Renner (2021):
iTaxoTools 0.1: Kickstarting a specimen-based software toolkit for taxonomists. - Megataxa 6: 77-92.</i>

Mold was developed by Alexander Fedosov, Guillaume Achaz, Andrey Gontchar, Nicolas Puillandre:

<i>Fedosov A.E., Achaz G., Gontchar A., Puillandre N. 2022. MOLD, a novel software to compile accurate and reliable DNA diagnoses for taxonomic descriptions. Molecular Ecology Resources, 22: 2038-2053. DOI: 10.1111/1755-0998.13590.</i>
