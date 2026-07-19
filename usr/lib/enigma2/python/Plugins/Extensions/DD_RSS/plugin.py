# -*- coding: utf-8 -*-

# based on the work from RSS Simple by DDamir v.0.2
# This Software is Free, use it where you want
# when you want for whatever you want and modify it if you want but don't remove my copyright!
# adapted for py3 and added fhd screens @lululla 20240524
# recode write @lululla 20240906
# fully rewritten for Python3 robustness 20260418

from Components.ActionMap import ActionMap, NumberActionMap
from Components.ConfigList import ConfigList
from Components.MenuList import MenuList
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.config import (
    ConfigText,
    KEY_0,
    KEY_DELETE,
    KEY_BACKSPACE,
    KEY_LEFT,
    KEY_RIGHT,
    getConfigListEntry,
)
from Plugins.Plugin import PluginDescriptor
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.VirtualKeyBoard import VirtualKeyBoard
from enigma import eTimer, getDesktop
import os
import ssl
import json
import html
import re
import subprocess
import threading
from collections import deque
from datetime import datetime
from urllib.request import urlopen, Request
from distutils.version import LooseVersion
import xml.etree.ElementTree as ET
from . import (
    _ as tr,
    __version__,
    b64decoder,
    descplug,
    installer_url,
    developer_url,
    HEADERS
)
from .Console import Console as xConsole
from .google_translate import trans

# ---------------------------
# Translation cache & async
# ---------------------------
_trans_cache = {}
_trans_queue = deque()
_trans_timer = None


def _process_translation_queue():
    # global _trans_timer
    if _trans_queue:
        text, callback = _trans_queue.popleft()

        def do_translate():
            translated = trans(text)
            _trans_cache[text] = translated
            # schedule callback in main thread
            t = eTimer()
            t.callback.append(lambda: callback(translated))
            t.start(0, True)
        threading.Thread(target=do_translate, daemon=True).start()
    if _trans_timer:
        _trans_timer.start(100, True)


def translate_async(text, callback):
    if not text:
        callback(text)
        return
    if text in _trans_cache:
        callback(_trans_cache[text])
        return
    _trans_queue.append((text, callback))
    global _trans_timer
    if _trans_timer is None:
        _trans_timer = eTimer()
        _trans_timer.callback.append(_process_translation_queue)
        _trans_timer.start(100, True)


screen_width = getDesktop(0).size().width()
ssl._create_default_https_context = ssl._create_unverified_context

FEEDS_FILE = '/var/ddRSS/feeds'
TMP_RSS_FILE = '/tmp/rsstr'
TMP_LIRSS_FILE = '/tmp/lirss'
TMP_FEEDS_XML = '/tmp/feeds.xml'


def decodeHtml(text):
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub('<[^>]+>', '', text)
    return text.strip()


def ensure_dir(path):
    dirname = os.path.dirname(path)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)


def trazenje(t1, t2, t3, text):
    n0 = text.find(t1)
    n1 = text.find(t2)
    n2 = text.find(t3)
    return (n0, n1, n2)


def uzmitekst(p0, p1, text):
    return text[p0:p1]


def skrati(d0, zl):
    return zl[d0:len(zl)]


# ----------------------------------------------------------------------
# UnesiPod - Add/Edit RSS feed
# ----------------------------------------------------------------------
class UnesiPod(Screen):
    def __init__(self, session, edit_name=None, edit_url=None):
        self.session = session
        self.edit_name = edit_name
        self.edit_url = edit_url

        if screen_width == 1280:
            self.skin = '''
                <screen name="UnesiPod" position="center,center" size="1280,720" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="645,25" zPosition="4" size="580,26" font="Regular;23" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="center,center" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="liste" itemHeight="36" font="Regular; 24" position="613,80" size="620,513" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 22" position="40,494" size="515,187" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="639,679" size="166,30" zPosition="4" font="Regular; 18" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="781,679" size="166,30" zPosition="4" font="Regular; 18" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="1056,680" size="166,30" zPosition="4" font="Regular; 20" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="912,680" size="166,30" zPosition="4" font="Regular; 20" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 26" halign="center" position="46,20" render="Label" size="499,46" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="51,101" zPosition="20" size="492,280" backgroundColor="transparent" transparent="0" />
                </screen>'''
        elif screen_width == 2560:
            self.skin = '''
                <screen name="UnesiPod" position="center,center" size="2560,1440" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="1290,50" zPosition="4" size="1160,53" font="Regular;47" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="center,center" size="2560,1440" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="liste" itemHeight="73" font="Regular; 48" position="1227,160" size="1240,1027" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 45" position="81,989" size="1031,375" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="1279,1359" size="333,60" zPosition="4" font="Regular; 37" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="1563,1359" size="333,60" zPosition="4" font="Regular; 37" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="2112,1360" size="333,60" zPosition="4" font="Regular; 40" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="1824,1360" size="333,60" zPosition="4" font="Regular; 40" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 53" halign="center" position="92,40" render="Label" size="999,93" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="103,203" zPosition="20" size="985,561" backgroundColor="transparent" transparent="0" />
                </screen>'''
        else:
            # FHD 1920x1080
            self.skin = '''
                <screen name="UnesiPod" position="center,center" size="1920,1080" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="968,38" zPosition="4" size="870,40" font="Regular;35" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="center,center" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="liste" itemHeight="55" font="Regular; 36" position="920,120" size="930,770" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 34" position="61,742" size="773,281" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="959,1019" size="250,45" zPosition="4" font="Regular; 28" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="1172,1019" size="250,45" zPosition="4" font="Regular; 28" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="1584,1020" size="250,45" zPosition="4" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="1369,1020" size="250,45" zPosition="4" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 40" halign="center" position="69,30" render="Label" size="749,70" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="77,152" zPosition="20" size="739,421" backgroundColor="transparent" transparent="0" />
                </screen>'''

        Screen.__init__(self, session)
        self["actions"] = NumberActionMap(
            ["SetupActions", "TextEntryActions", "WizardActions", "HelpActions",
             "DirectionActions", "InfobarEPGActions", "ChannelSelectBaseActions",
             "MediaPlayerActions", "VirtualKeyboardActions", "HotkeyActions"],
            {
                "cancel": self.close,
                "ok": self.gotovo,
                "left": self.keyLeft,
                "right": self.keyRight,
                "deleteForward": self.keyDelete,
                "deleteBackward": self.keyBackspace,
                "blue": self.openKeyboard,
                "green": self.save,
                "showVirtualKeyboard": self.openKeyboard,
                "yellow": self.update_me,
                "yellow_long": self.update_dev,
                "info_long": self.update_dev,
                "infolong": self.update_dev,
                "showEventInfoPlugin": self.update_dev,
                "0": self.keyNumber,
                "1": self.keyNumber,
                "2": self.keyNumber,
                "3": self.keyNumber,
                "4": self.keyNumber,
                "5": self.keyNumber,
                "6": self.keyNumber,
                "7": self.keyNumber,
                "8": self.keyNumber,
                "9": self.keyNumber,
            }, -1
        )

        self["key_red"] = StaticText(tr("Close"))
        self["key_green"] = StaticText(tr("Save"))
        self["key_blue"] = StaticText(tr("Keyboard"))
        self["key_yellow"] = StaticText(tr("Update"))
        self["info"] = StaticText(tr("Select"))
        self["opisi"] = StaticText(tr('Setup RSS FEED v.%s' % __version__))
        self.nazrss = ConfigText(fixed_size=False, visible_width=40)
        self.urlrss = ConfigText(fixed_size=False, visible_width=40)
        if self.edit_name:
            self.nazrss.value = self.edit_name
        if self.edit_url:
            self.urlrss.value = self.edit_url.replace('http://', '')

        config_list = [
            getConfigListEntry('RSS name: ', self.nazrss),
            getConfigListEntry('URL=>http://: ', self.urlrss)
        ]
        self['liste'] = ConfigList(config_list)
        self.update_timer = eTimer()
        self.update_timer.callback.append(self.check_version)
        self.update_timer.start(500, True)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        self.setTitle('RSS FEED')

    def check_version(self):
        remote_version = '0.0'
        remote_changelog = ''
        try:
            req = Request(
                b64decoder(installer_url), headers={
                    'User-Agent': 'Mozilla/5.0'})
            page = urlopen(
                req, timeout=10).read().decode(
                'utf-8', errors='ignore')
            for line in page.split('\n'):
                if line.startswith("version"):
                    remote_version = line.split(
                        "'")[1] if "'" in line else line.split('=')[1].strip()
                elif line.startswith("changelog"):
                    remote_changelog = line.split(
                        "'")[1] if "'" in line else line.split('=')[1].strip()
                    break
            if LooseVersion(__version__) < LooseVersion(remote_version):
                self.update_available = True
                self.new_version = remote_version
                self.new_changelog = remote_changelog
                self.session.open(
                    MessageBox,
                    tr('New version %s is available\n\nChangelog: %s\n\nPress info_long or yellow_long button to start force updating.') %
                    (self.new_version,
                     self.new_changelog),
                    MessageBox.TYPE_INFO,
                    timeout=5)
        except Exception as e:
            print("Version check error:", e)

    def update_me(self):
        if hasattr(self, 'update_available') and self.update_available:
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                tr("New version %s is available.\n\nChangelog: %s \n\nDo you want to install it now?") %
                (self.new_version,
                 self.new_changelog),
                MessageBox.TYPE_YESNO)
        else:
            self.session.open(
                MessageBox,
                tr("Congrats! You already have the latest version..."),
                MessageBox.TYPE_INFO,
                timeout=4)

    def update_dev(self):
        try:
            req = Request(
                b64decoder(developer_url), headers={
                    'User-Agent': 'Mozilla/5.0'})
            page = urlopen(req, timeout=10).read().decode('utf-8')
            data = json.loads(page)
            remote_date = data['pushed_at']
            strp_remote_date = datetime.strptime(
                remote_date, '%Y-%m-%dT%H:%M:%SZ')
            remote_date_str = strp_remote_date.strftime('%Y-%m-%d')
            self.session.openWithCallback(
                self.install_update,
                MessageBox,
                tr("Do you want to install update ( %s ) now?") %
                remote_date_str,
                MessageBox.TYPE_YESNO)
        except Exception as e:
            print('Update dev error:', e)
            self.session.open(
                MessageBox,
                tr("Update check failed!"),
                MessageBox.TYPE_ERROR,
                timeout=3)

    def install_update(self, answer=False):
        if answer:
            cmd = 'wget -q "--no-check-certificate" ' + \
                b64decoder(installer_url) + ' -O - | /bin/sh'
            self.session.open(
                xConsole,
                'Upgrading...',
                cmdlist=[cmd],
                finishedCallback=self.update_callback,
                closeOnSuccess=False)
        else:
            self.session.open(
                MessageBox,
                tr("Update Aborted!"),
                MessageBox.TYPE_INFO,
                timeout=3)

    def update_callback(self, result=None):
        print('Update result:', result)

    def openKeyboard(self):
        current = self['liste'].getCurrent()
        if current and current[1] == self.nazrss:
            self.session.openWithCallback(
                self.vrationazad,
                VirtualKeyBoard,
                title='RSS name',
                text=self.nazrss.value)
        elif current and current[1] == self.urlrss:
            self.session.openWithCallback(
                self.vrationazad,
                VirtualKeyBoard,
                title='URL -> http://',
                text=self.urlrss.value)

    def vrationazad(self, callback=None):
        if callback:
            current = self['liste'].getCurrent()
            if current and current[1] == self.nazrss:
                self.nazrss.value = callback
            elif current and current[1] == self.urlrss:
                self.urlrss.value = callback

    def keyLeft(self):
        self['liste'].handleKey(KEY_LEFT)

    def keyRight(self):
        self['liste'].handleKey(KEY_RIGHT)

    def keyDelete(self):
        self['liste'].handleKey(KEY_DELETE)

    def keyBackspace(self):
        self['liste'].handleKey(KEY_BACKSPACE)

    def keyNumber(self, number):
        self['liste'].handleKey(KEY_0 + number)

    def gotovo(self):
        self.close()

    def save(self):
        ensure_dir(FEEDS_FILE)
        with open(FEEDS_FILE, 'a') as fp:
            title = str(self.nazrss.value)
            lnk = str(self.urlrss.value)
            fp.write(f"{title}:http://{lnk}\n")
        self.gotovo()


# ----------------------------------------------------------------------
# MojRSS - Main screen
# ----------------------------------------------------------------------
class MojRSS(Screen):
    def __init__(self, session):
        self.session = session
        if screen_width == 1280:
            self.skin = '''
                <screen name="MojRSS" position="center,center" size="1280,720" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="645,25" zPosition="4" size="580,26" font="Regular;23" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="125,61" size="333,5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsslist" itemHeight="36" font="Regular; 24" position="613,80" size="620,513" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 22" position="40,494" size="515,187" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="639,679" size="166,30" zPosition="4" font="Regular; 18" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="781,679" size="166,30" zPosition="4" font="Regular; 18" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="916,679" size="166,30" zPosition="4" font="Regular; 18" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="1056,680" size="166,30" zPosition="4" font="Regular; 20" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 26" halign="center" position="46,20" render="Label" size="499,46" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="51,101" zPosition="20" size="492,280" backgroundColor="transparent" transparent="0" />
                </screen>'''
        elif screen_width == 2560:
            self.skin = '''
                <screen name="MojRSS" position="center,center" size="2560,1440" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="1290,50" zPosition="4" size="1160,53" font="Regular;47" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="250,123" size="667,11" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="2560,1440" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsslist" itemHeight="73" font="Regular; 48" position="1227,160" size="1240,1027" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 45" position="81,989" size="1031,375" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="1279,1359" size="333,60" zPosition="4" font="Regular; 37" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="1563,1359" size="333,60" zPosition="4" font="Regular; 37" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="1832,1359" size="333,60" zPosition="4" font="Regular; 37" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="2112,1360" size="333,60" zPosition="4" font="Regular; 40" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 53" halign="center" position="92,40" render="Label" size="999,93" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="103,203" zPosition="20" size="985,561" backgroundColor="transparent" transparent="0" />
                </screen>'''
        else:
            # FHD
            self.skin = '''
                <screen name="MojRSS" position="center,center" size="1920,1080" title="RSS FEED" flags="wfNoBorder">
                    <widget name="info" position="968,38" zPosition="4" size="870,40" font="Regular;35" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="188,92" size="500,8" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsslist" itemHeight="55" font="Regular; 36" position="920,120" size="930,770" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 34" position="61,742" size="773,281" zPosition="2" transparent="1" />
                    <widget source="key_red" render="Label" position="959,1019" size="250,45" zPosition="4" font="Regular; 28" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_green" render="Label" position="1172,1019" size="250,45" zPosition="4" font="Regular; 28" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_yellow" render="Label" position="1374,1019" size="250,45" zPosition="4" font="Regular; 28" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget source="key_blue" render="Label" position="1584,1020" size="250,45" zPosition="4" font="Regular; 30" valign="center" halign="center" backgroundColor="#050c101b" transparent="1" foregroundColor="white" />
                    <widget font="Regular; 40" halign="center" position="69,30" render="Label" size="749,70" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="77,152" zPosition="20" size="739,421" backgroundColor="transparent" transparent="0" />
                </screen>'''

        Screen.__init__(self, session)
        self["actions"] = ActionMap(
            ["OkCancelActions", "DirectionActions", "ColorActions", "MovieSelectionActions",
             "WizardActions", "EPGSelectActions", "InputActions", "NumberActions"],
            {
                "ok": self.okClicked,
                "cancel": self.izlaz,
                "0": self.reload,
                "green": self.green,
                "red": self.red,
                "yellow": self.yellow,
                "blue": self.blue,
            }, -1
        )
        self.ime = []
        self.put = []
        self.rsslist = []
        self["key_red"] = StaticText(tr("Delete"))
        self["key_green"] = StaticText(tr("Add"))
        self["key_yellow"] = StaticText(tr("Edit"))
        self["key_blue"] = StaticText(tr("Import"))
        self["info"] = StaticText(tr("Select"))
        self["opisi"] = StaticText(descplug)
        self["rsslist"] = MenuList([])

        ensure_dir(FEEDS_FILE)
        self.load_feeds()

        self.timer = eTimer()
        self.timer.callback.append(self.showMenu)
        self.timer.start(200, True)

    def load_feeds(self):
        self.ime = []
        self.put = []
        self.rsslist = []
        if os.path.exists(FEEDS_FILE):
            try:
                with open(FEEDS_FILE, 'r') as fp:
                    for line in fp:
                        line = line.strip()
                        if line and ':' in line:
                            name, url = line.split(':', 1)
                            self.ime.append(name.strip())
                            self.put.append(url.strip())
                            self.rsslist.append(
                                f"*** {name.strip()} ***".center(90))
            except Exception as e:
                print('Error reading feeds:', e)

    def save_feeds(self):
        ensure_dir(FEEDS_FILE)
        with open(FEEDS_FILE, 'w') as fp:
            for name, url in zip(self.ime, self.put):
                fp.write(f"{name}:{url}\n")

    def red(self):
        selindex = self['rsslist'].getSelectedIndex()
        if selindex is not None and 0 <= selindex < len(self.ime):
            del self.ime[selindex]
            del self.put[selindex]
            self.load_feeds()
            self.showMenu()

    def yellow(self):
        selindex = self['rsslist'].getSelectedIndex()
        if selindex is not None and 0 <= selindex < len(self.ime):
            name = self.ime[selindex]
            url = self.put[selindex]
            self.session.openWithCallback(self.reload, UnesiPod, name, url)

    def green(self):
        self.session.openWithCallback(self.reload, UnesiPod)

    def reload(self):
        self.load_feeds()
        self.showMenu()

    def blue(self):
        if os.path.exists(TMP_FEEDS_XML):
            self.import_from_xml()
        else:
            self.session.open(
                MessageBox,
                tr("No XML file found at /tmp/feeds.xml"),
                MessageBox.TYPE_INFO,
                timeout=5)

    def import_from_xml(self):
        try:
            with open(TMP_FEEDS_XML, 'r') as fp:
                content = fp.read()
            name_pattern = re.compile(r'<name>(.*?)</name>', re.I)
            url_pattern = re.compile(r'<url>(.*?)</url>', re.I)
            names = name_pattern.findall(content)
            urls = url_pattern.findall(content)
            if names and urls and len(names) == len(urls):
                for n, u in zip(names, urls):
                    if n.strip() and u.strip():
                        self.ime.append(n.strip())
                        self.put.append(u.strip())
                self.save_feeds()
                self.load_feeds()
                self.showMenu()
                self.session.open(
                    MessageBox,
                    tr("Feeds imported successfully"),
                    MessageBox.TYPE_INFO,
                    timeout=3)
            else:
                raise ValueError("Invalid XML structure")
        except Exception as e:
            print("Import error:", e)
            self.session.open(
                MessageBox,
                tr("Failed to parse XML file"),
                MessageBox.TYPE_ERROR,
                timeout=5)

    def izlaz(self):
        self.save_feeds()
        if self.timer:
            self.timer.stop()
        self.close()

    def showMenu(self):
        self['rsslist'].setList(self.rsslist)
        self["opisi"].setText(descplug)

    def okClicked(self):
        selindex = self['rsslist'].getSelectedIndex()
        if selindex is None or selindex >= len(self.put):
            return
        url = self.put[selindex]

        print("[RSS] Selected URL:", url)  # DEBUG

        try:
            req = Request(url, headers=HEADERS)
            print("[RSS] Request headers:", req.headers)  # DEBUG
            response = urlopen(req, timeout=10)
            content = response.read().decode('utf-8', errors='ignore')
            print("[RSS] Downloaded %d bytes" % len(content))  # DEBUG
            with open(TMP_RSS_FILE, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print("[RSS] Download error:", e)  # DEBUG
            self.session.open(
                MessageBox,
                tr("Download failed: {}").format(str(e)),
                MessageBox.TYPE_ERROR,
                timeout=3)
            return

        try:
            tree = ET.parse(TMP_RSS_FILE)
            root = tree.getroot()

            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'dc': 'http://purl.org/dc/elements/1.1/',
                'content': 'http://purl.org/rss/1.0/modules/content/',
                'slash': 'http://purl.org/rss/1.0/modules/slash/'
            }

            channel = root.find('channel')
            if channel is None:
                channel = root

            feed_title = channel.findtext('title', 'RSS Feed')
            feed_title = decodeHtml(feed_title)

            with open(TMP_LIRSS_FILE, 'w', encoding='utf-8') as fp1:
                fp1.write(f'0<DD>UTF-8<DD>{feed_title}<DD>nessuno\n')

                for item in channel.findall('item'):
                    title_elem = item.find('title')
                    title = decodeHtml(
                        title_elem.text) if title_elem is not None and title_elem.text else 'No title'

                    pubdate_elem = item.find('pubDate')
                    pubdate = decodeHtml(
                        pubdate_elem.text) if pubdate_elem is not None and pubdate_elem.text else 'No date'

                    desc = ''
                    content_elem = item.find('content:encoded', ns)
                    if content_elem is not None and content_elem.text:
                        desc = decodeHtml(content_elem.text)
                    else:
                        desc_elem = item.find('description')
                        if desc_elem is not None and desc_elem.text:
                            desc = decodeHtml(desc_elem.text)

                    img = 'nessuna'
                    if desc:
                        img_match = re.search(
                            r'src=["\']([^"\']+)["\']', desc, re.I)
                        if img_match:
                            img = img_match.group(1)

                    fp1.write(f'{title}<DD>{pubdate}<DD>{desc}<DD>{img}\n')

            self.session.open(PregledRSS)

        except ET.ParseError as e:
            print('XML Parse error:', e)
            self.session.open(
                MessageBox,
                tr("Invalid XML feed: {}").format(str(e)),
                MessageBox.TYPE_ERROR,
                timeout=5)
        except Exception as e:
            print('Parse error:', e)
            self.session.open(
                MessageBox,
                tr("Failed to parse RSS feed: {}").format(str(e)),
                MessageBox.TYPE_ERROR,
                timeout=5)


# ----------------------------------------------------------------------
# PregledRSS - Preview RSS items
# ----------------------------------------------------------------------
class PregledRSS(Screen):
    def __init__(self, session):
        self.session = session
        self.current_index = 0
        self.prviput = 0
        self.rsslist = []
        self.itemnas = []
        self.datum = []
        self.desc = []
        self.slika = []
        self.feed_title = ""
        if screen_width == 1280:
            self.skin = '''
                <screen name="PregledRSS" position="center,center" size="1280,720" title="RSS FEED">
                    <widget name="info" position="645,25" zPosition="4" size="580,26" font="Regular;23" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="125,61" size="333,5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsspreg" itemHeight="36" font="Regular; 24" position="613,80" size="620,513" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 22" position="40,494" size="515,187" zPosition="2" transparent="1" />
                    <widget font="Regular; 26" halign="center" position="46,20" render="Label" size="499,46" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="51,101" zPosition="20" size="492,280" backgroundColor="transparent" transparent="0" />
                </screen>'''
        elif screen_width == 2560:
            self.skin = '''
                <screen name="PregledRSS" position="center,center" size="2560,1440" title="RSS FEED">
                    <widget name="info" position="1290,50" zPosition="2" size="1160,53" font="Regular;47" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="250,123" size="667,11" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="2560,1440" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsspreg" itemHeight="73" font="Regular; 45" position="1227,160" size="1240,1027" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 45" position="81,989" size="1031,375" zPosition="2" transparent="1" />
                    <widget font="Regular; 53" halign="center" position="92,40" render="Label" size="999,93" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="103,203" zPosition="20" size="985,561" backgroundColor="transparent" transparent="0" />
                </screen>'''
        else:
            # FHD
            self.skin = '''
                <screen name="PregledRSS" position="center,center" size="1920,1080" title="RSS FEED">
                    <widget name="info" position="968,38" zPosition="2" size="870,40" font="Regular;35" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="188,92" size="500,8" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="rsspreg" itemHeight="55" font="Regular; 34" position="920,120" size="930,770" scrollbarMode="showOnDemand" zPosition="2" transparent="1" />
                    <widget name="opisi" font="Regular; 34" position="61,742" size="773,281" zPosition="2" transparent="1" />
                    <widget font="Regular; 40" halign="center" position="69,30" render="Label" size="749,70" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="77,152" zPosition="20" size="739,421" backgroundColor="transparent" transparent="0" />
                </screen>'''

        Screen.__init__(self, session)
        self['actions'] = NumberActionMap(
            ['SetupActions', 'DirectionActions', 'ListboxActions'],
            {
                'up': self.keyUp,
                'down': self.keyDown,
                'left': self.pageUp,
                'right': self.pageDown,
                'upRepeated': self.keyUp,
                'downRepeated': self.keyDown,
                'leftRepeated': self.keyUp,
                'rightRepeated': self.keyDown,
                'pageUp': self.pageUp,
                'pageDown': self.pageDown,
                'ok': self.ok,
                'cancel': self.izlaz
            }, -2
        )
        self['info'] = StaticText(tr('Select'))
        self['opisi'] = ScrollLabel()
        self['rsspreg'] = MenuList([])

        self.timer = eTimer()
        self.timer.callback.append(self.showMenu)
        self.timer.start(200, True)

    def stvorilistu(self):
        self.itemnas = []
        self.datum = []
        self.desc = []
        self.slika = []
        self.rsslist = []
        if os.path.exists(TMP_LIRSS_FILE):
            try:
                with open(TMP_LIRSS_FILE, 'r', encoding='utf-8') as fp:
                    lines = fp.read().split('\n')
                    prvi = 1
                    for line in lines:
                        if not line.strip():
                            continue
                        razbi = line.split('<DD>')
                        if len(razbi) < 4:
                            continue
                        if prvi == 1:
                            prvi = 0
                            self.feed_title = razbi[2] if len(
                                razbi) > 2 else "RSS Feed"
                        else:
                            self.itemnas.append(razbi[0])
                            self.datum.append(decodeHtml(razbi[1]))
                            self.desc.append(decodeHtml(razbi[2]))
                            self.slika.append(razbi[3])
                            self.rsslist.append(razbi[0])
            except Exception as e:
                print("Error reading /tmp/lirss:", e)
        self['rsspreg'].setList(self.rsslist)

    def showMenu(self):
        if self.prviput == 0:
            self.prviput = 1
            self.stvorilistu()
            # Traduci tutto subito (con cache)
            self.feed_title = trans(self.feed_title)
            for i in range(len(self.datum)):
                self.datum[i] = trans(self.datum[i])
                self.desc[i] = trans(self.desc[i])
            # Mostra il primo elemento
            if len(self.rsslist) > 0:
                self.setTitle(self.feed_title)
                self['opisi'].setText(f"{self.datum[0]}\n\n{self.desc[0]}")
        else:
            if 0 <= self.current_index < len(self.rsslist):
                self.setTitle(self.feed_title)
                self['opisi'].setText(
                    f"{self.datum[self.current_index]}\n\n{self.desc[self.current_index]}")

    def keyUp(self):
        if self.current_index > 0:
            self.current_index -= 1
            self['rsspreg'].up()
            self.showMenu()

    def keyDown(self):
        if self.current_index < len(self.rsslist) - 1:
            self.current_index += 1
            self['rsspreg'].down()
            self.showMenu()

    def pageUp(self):
        self['opisi'].pageUp()

    def pageDown(self):
        self['opisi'].pageDown()

    def ok(self):
        if 0 <= self.current_index < len(self.itemnas):
            self.session.open(CijeliTekst,
                              self.itemnas[self.current_index],
                              self.desc[self.current_index])

    def izlaz(self):
        if self.timer:
            self.timer.stop()
        self.close()


# ----------------------------------------------------------------------
# CijeliTekst - Full article view
# ----------------------------------------------------------------------
class CijeliTekst(Screen):
    def __init__(self, session, title, description):
        if screen_width == 1280:
            self.skin = '''
                <screen name="CijeliTekst" position="center,center" size="1280,720" title="RSS FEED">
                    <widget name="info" position="645,25" zPosition="4" size="580,26" font="Regular;23" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="125,61" size="333,5" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1280,720" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="opisi" font="Regular; 24" position="613,80" size="620,513" zPosition="2" transparent="1" />
                    <widget font="Regular; 26" halign="center" position="46,20" render="Label" size="499,46" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="51,101" zPosition="20" size="492,280" backgroundColor="transparent" transparent="0" />
                </screen>'''
        elif screen_width == 2560:
            self.skin = '''
                <screen name="CijeliTekst" position="center,center" size="2560,1440" title="RSS FEED">
                    <widget name="info" position="1290,50" zPosition="4" size="1160,53" font="Regular;47" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="250,123" size="667,11" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="2560,1440" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="opisi" font="Regular; 48" position="1227,160" size="1240,1027" zPosition="2" transparent="1" />
                    <widget font="Regular; 53" halign="center" position="92,40" render="Label" size="999,93" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="103,203" zPosition="20" size="985,561" backgroundColor="transparent" transparent="0" />
                </screen>'''
        else:
            # FHD
            self.skin = '''
                <screen name="CijeliTekst" position="center,center" size="1920,1080" title="RSS FEED">
                    <widget name="info" position="968,38" zPosition="4" size="870,40" font="Regular;35" backgroundColor="#050c101b" foregroundColor="white" transparent="1" valign="center" />
                    <ePixmap position="188,92" size="500,8" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/slider_fhd.png" scale="1" alphatest="blend" />
                    <ePixmap position="center,center" size="1920,1080" zPosition="-1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/DD_RSS/images/RSS_FEED+1.png" scale="1" transparent="1" alphatest="blend" />
                    <widget name="opisi" font="Regular; 36" position="920,120" size="930,770" zPosition="2" transparent="1" />
                    <widget font="Regular; 40" halign="center" position="69,30" render="Label" size="749,70" source="global.CurrentTime" transparent="1">
                        <convert type="ClockToText">Format:%a %d.%m. %Y | %H:%M</convert>
                    </widget>
                    <widget source="session.VideoPicture" render="Pig" position="77,152" zPosition="20" size="739,421" backgroundColor="transparent" transparent="0" />
                </screen>'''

        Screen.__init__(self, session)
        self.title = title
        self.description = description
        self['opisi'] = ScrollLabel()
        self['info'] = StaticText(tr('Select'))
        self["shortcuts"] = ActionMap(["WizardActions", "SetupActions"], {
            "up": self.pageUp,
            "down": self.pageDown,
            "cancel": self.close,
            "ok": self.close,
        }, -1)

        # show original immediately
        self['opisi'].setText(decodeHtml(description))
        self.setTitle(title)
        # then translate in background
        translate_async(description, self._update_description)
        translate_async(title, self._update_title)

    def _update_description(self, translated):
        self['opisi'].setText(translated)

    def _update_title(self, translated):
        self.setTitle(translated)

    def pageUp(self):
        self['opisi'].pageUp()

    def pageDown(self):
        self['opisi'].pageDown()


# ----------------------------------------------------------------------
# Plugin entry points
# ----------------------------------------------------------------------
def main(session, **kwargs):
    session.open(MojRSS)


def Plugins(**kwargs):
    return [
        PluginDescriptor(
            name='RSS by DD',
            description='RSS Simple by DDamir ver.%s' % __version__,
            icon='rss.png',
            where=PluginDescriptor.WHERE_PLUGINMENU,
            fnc=main),
        PluginDescriptor(
            name='RSS by DD',
            description='RSS Simple by DDamir ver.%s' % __version__,
            icon='rss.png',
            where=PluginDescriptor.WHERE_EXTENSIONSMENU,
            fnc=main)
    ]
