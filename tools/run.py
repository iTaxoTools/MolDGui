#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Launch the Hapsolutely GUI"""

import multiprocessing

from itaxotools.mold.gui import run

if __name__ == "__main__":
    multiprocessing.freeze_support()
    run()
