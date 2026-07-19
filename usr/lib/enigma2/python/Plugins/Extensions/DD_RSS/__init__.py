#!/usr/bin/python3
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import gettext
import base64

__author__ = "Lululla"
__email__ = "ekekaz@gmail.com"
__copyright__ = "Copyright (c) 2024 Lululla"
__license__ = "GPL-v2"
__version__ = "1.1"
DEBUG = True
SYSTEM_DIR = '/etc/enigma2/apod'

descplugx = 'RSS Simmple by DDamir v.%s\n\nadapted for py3 by @lululla 20260418\n\n' % __version__
inff = 'Import New from /tmp/feeds.xml'
descplug = descplugx + inff
installer_url = 'aHR0cHM6Ly9yYXcuZ2l0aHVidXNlcmNvbnRlbnQuY29tL0JlbGZhZ29yMjAwNS9ERFJTU1JlYWRlci9tYWluL2luc3RhbGxlci5zaA=='
developer_url = 'aHR0cHM6Ly9hcGkuZ2l0aHViLmNvbS9yZXBvcy9CZWxmYWdvcjIwMDUvRERSU1NSZWFkZXI='


PluginLanguageDomain = 'DD_RSS'
PluginLanguagePath = 'Extensions/DD_RSS/locale'
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}


def getDesktopSize():
    from enigma import getDesktop
    s = getDesktop(0).size()
    return (s.width(), s.height())


def isWQHD():
    """2560 x 1440 (WQHD)"""
    width, height = getDesktopSize()
    return width == 2560 and height == 1440


def isUHD():
    """3840 x 2160 (4K UHD)"""
    width, height = getDesktopSize()
    return width == 3840 and height == 2160


def isFHD():
    """1920 x 1080 (Full HD)"""
    width, height = getDesktopSize()
    return width == 1920 and height == 1080


def isHD():
    """1280 x 720 (HD)"""
    width, height = getDesktopSize()
    return width == 1280 and height == 720


def b64decoder(data):
    """Robust base64 decoding with padding correction"""
    data = data.strip()
    pad = len(data) % 4
    if pad == 1:  # Invalid base64 length
        return ""
    if pad:
        data += "=" * (4 - pad)
    try:
        decoded = base64.b64decode(data)
        return decoded.decode('utf-8')
    except Exception as e:
        print("Base64 decoding error: %s" % e)
        return ""


def paypal():
    conthelp = "If you like what I do you\n"
    conthelp += "can contribute with a coffee\n"
    conthelp += "scan the qr code and donate € 1.00"
    return conthelp


def localeInit():
    gettext.bindtextdomain(
        PluginLanguageDomain,
        resolveFilename(
            SCOPE_PLUGINS,
            PluginLanguagePath))


def _(txt):
    translated = gettext.dgettext(PluginLanguageDomain, txt)
    if translated:
        return translated
    else:
        return gettext.gettext(txt)


localeInit()
language.addCallback(localeInit)
