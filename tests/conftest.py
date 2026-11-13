# Copyright (C) 2026 Julie C. Libarkin
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests read the library snapshot in library/, never the published library, so they don't use the network."""
import os

os.environ["HUMETA_LIBRARY_SNAPSHOT"] = "1"
