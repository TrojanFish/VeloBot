# -*- coding: utf-8 -*-

from .en import LOCALIZATION as en_loc, LOCALIZED_COMMANDS as en_cmd, LOCALIZED_ACHIEVEMENTS as en_ach
from .zh_hans import LOCALIZATION as zh_hans_loc, LOCALIZED_COMMANDS as zh_hans_cmd, LOCALIZED_ACHIEVEMENTS as zh_hans_ach
from .zh_hant import LOCALIZATION as zh_hant_loc, LOCALIZED_COMMANDS as zh_hant_cmd, LOCALIZED_ACHIEVEMENTS as zh_hant_ach
from .es import LOCALIZATION as es_loc, LOCALIZED_COMMANDS as es_cmd, LOCALIZED_ACHIEVEMENTS as es_ach
from .de import LOCALIZATION as de_loc, LOCALIZED_COMMANDS as de_cmd, LOCALIZED_ACHIEVEMENTS as de_ach
from .fr import LOCALIZATION as fr_loc, LOCALIZED_COMMANDS as fr_cmd, LOCALIZED_ACHIEVEMENTS as fr_ach
from .it import LOCALIZATION as it_loc, LOCALIZED_COMMANDS as it_cmd, LOCALIZED_ACHIEVEMENTS as it_ach

LOCALIZATION = {
    'en': en_loc,
    'zh-hans': zh_hans_loc,
    'zh-hant': zh_hant_loc,
    'es': es_loc,
    'de': de_loc,
    'fr': fr_loc,
    'it': it_loc,
}

LOCALIZED_COMMANDS = {
    'en': en_cmd,
    'zh-hans': zh_hans_cmd,
    'zh-hant': zh_hant_cmd,
    'es': es_cmd,
    'de': de_cmd,
    'fr': fr_cmd,
    'it': it_cmd,
}

LOCALIZED_ACHIEVEMENTS = {
    'en': en_ach,
    'zh-hans': zh_hans_ach,
    'zh-hant': zh_hant_ach,
    'es': es_ach,
    'de': de_ach,
    'fr': fr_ach,
    'it': it_ach,
}
