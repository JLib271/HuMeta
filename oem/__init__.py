# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Core logic for the Open Educational Metadata platform.

Everything in this package is plain Python with no Streamlit dependency, so it
can be unit-tested and reused (for example by a command-line tool or a
different front end). The Streamlit app in ``openscience.py`` imports it.

Modules
-------
library   Load the instrument library (instruments, items, constructs,
          response scales, standard variables) from ``library/``.
naming    Rules for generating and checking shared variable names.
codebook  Build and export codebooks (data dictionaries) for a study.
"""

__all__ = ["library", "naming", "codebook"]
