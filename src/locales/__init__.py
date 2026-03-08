# -*- coding: utf-8 -*-

from .en import LOCALIZATION as en_loc, LOCALIZED_COMMANDS as en_cmd, LOCALIZED_ACHIEVEMENTS as en_ach
from .zh_hans import LOCALIZATION as zh_loc, LOCALIZED_COMMANDS as zh_cmd, LOCALIZED_ACHIEVEMENTS as zh_ach

LOCALIZATION = {
    'en': en_loc,
    'zh-hans': zh_loc
}

LOCALIZED_COMMANDS = {
    'en': en_cmd,
    'zh-hans': zh_cmd
}

LOCALIZED_ACHIEVEMENTS = {
    'en': en_ach,
    'zh-hans': zh_ach
}
