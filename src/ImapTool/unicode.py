####################################################################################################
#
# imap-tool -
# Copyright (C) 2026 Fabrice SALVAIRE
# SPDX-License-Identifier: GPL-3.0-or-later
#
####################################################################################################

__all__ = ['collator']

####################################################################################################

import icu
# from icu import Collator, Locale  # To sort correctly latin and unicode

####################################################################################################

# Fixme:
collator = icu.Collator.createInstance(icu.Locale('fr_FR'))  # ty:ignore[unresolved-attribute]
