#!/usr/bin/env python
import atexit
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap


python3 = sys.version_info.major == 3

if python3:
    import urllib.request
    urllib = urllib.request
else:
    import urllib


#### SETTINGS ####
settings = {
    "chrome": {
        "url": "http://dl.google.com/chrome/install/latest/chrome_installer.exe",
        "install_arguments": "/silent /install"
    },

    "firefox": {
        "pattern": "https://download.*os=win64.*lang=sv-SE",
        "url": "https://www.mozilla.org/en-US/firefox/all/",
        "install_arguments": "-ms"
    },

    "nodejs": {
        "pattern": '(node-v.*-x64.msi)"',
        "url": "https://nodejs.org/dist/latest-boron",
        "install_arguments": ""
    },

    "git": {
        "pattern": "https://github.com.*windows.*-64-bit.exe",
        "url": "https://git-scm.com/download/win",
        "install_arguments": '/SILENT /PathOption=CmdTools'
    },

    "graphicsmagick": {
        "url": "http://sourceforge.mirrorservice.org/g/gr/graphicsmagick/graphicsmagick-binaries/1.3.25/GraphicsMagick-1.3.25-Q8-win64-dll.exe",
        "install_arguments": '/SILENT /DIR="%programfiles%\GraphicsMagick"'
    }
}

registry_changes_to_perform = [
    {
        "name": "fix ie bfcache issue x86",
        "key": "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Internet Explorer\\MAIN\\FeatureControl\\FEATURE_BFCACHE]",
        "value": '"iexplore.exe"=dword:00000000'
    },
    {
        "name": "fix ie bfcache issue x64",
        "key": "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Wow6432Node\\Microsoft\\Internet Explorer\\MAIN\\FeatureControl\\FEATURE_BFCACHE]",
        "value": '"iexplore.exe"=dword:00000000'
    },
    {
        "name": "remove ie default browser message",
        "key": "[HKEY_CURRENT_USER\\Software\\Microsoft\\Internet Explorer\\Main]",
        "value": '"Check_Associations"="no"'
    },
    {
        "name": "ie protected mode for all zones (zone 1)",
        "key": "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\1]",
        "value": '"2500"=dword:00000000'
    },
    {
        "name": "ie protected mode for all zones (zone 2)",
        "key": "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\2]",
        "value": '"2500"=dword:00000000'
    },
    {
        "name": "ie protected mode for all zones (zone 3)",
        "key": "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\3]",
        "value": '"2500"=dword:00000000'
    },
    {
        "name": "ie protected mode for all zones (zone 4)",
        "key": "[HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Internet Settings\\Zones\\4]",
        "value": '"2500"=dword:00000000'
    }
]


temporary_path = tempfile.mkdtemp()
##################


def clean_up():
    if os.path.isdir(temporary_path):
        shutil.rmtree(temporary_path)

atexit.register(clean_up)


def perform_registry_changes():
    reg_filename = os.path.join(temporary_path, "registry_changes.reg")

    with open(reg_filename, "w") as regfile:
        regfile.write("Windows Registry Editor Version 5.00\n")

        for change in registry_changes_to_perform:
            regfile.write("{key}\n{value}\n\n".format(
                key=change["key"],
                value=change["value"]
            ))

    process = subprocess.Popen("reg import {0}".format(reg_filename))
    process.communicate()

    if process.returncode != 0:
        sys.exit("Failed to perform registry settings!")


def disable_import_wizard_for_firefox():
    path_to_autoconfig_js =\
        os.path.join(os.environ["programfiles"], "Mozilla Firefox", "defaults", "pref", "autoconfig.js")

    autoconfig_js = """
    // Any comment. See https://developer.mozilla.org/en-US/Firefox/Enterprise_deployment for more info.
    pref("general.config.filename", "mozilla.cfg");
    pref("general.config.obscure_value", 0);
    """.split("\n", 1)[1]

    path_to_mozilla_cfg =\
        os.path.join(os.environ["programfiles"], "Mozilla Firefox", "mozilla.cfg")

    mozilla_cfg = """
    // Disable Add-ons compatibility checking
    clearPref("extensions.lastAppVersion");

    // Don't show 'know your rights' on first run
    pref("browser.rights.3.shown", true);

    // Don't show WhatsNew on first run after every update
    pref("browser.startup.homepage_override.mstone","ignore");

    // Disable default browser check
    pref("browser.shell.checkDefaultBrowser", false);

    // Don't ask to install the Flash plugin
    pref("plugins.notifyMissingFlash", false);

    //Disable plugin checking
    lockPref("plugins.hide_infobar_for_outdated_plugin", true);
    clearPref("plugins.update.url");

    // Disable all data upload (Telemetry and FHR)
    lockPref("datareporting.policy.dataSubmissionEnabled", false);

    // Disable crash reporter
    lockPref("toolkit.crashreporter.enabled", false);
    Components.classes["@mozilla.org/toolkit/crash-reporter;1"].getService(Components.interfaces.nsICrashReporter).submitReports = false;
    """.split("\n", 1)[1]

    with open(path_to_autoconfig_js, "w") as autoconfig:
        autoconfig.write(textwrap.dedent(autoconfig_js))

    with open(path_to_mozilla_cfg, "w") as mozilla:
        mozilla.write(textwrap.dedent(mozilla_cfg))


def retrieve_firefox_download_url():
    url = settings["firefox"]["url"]

    try:
        data = urllib.urlopen(url).read()
    except:
        sys.exit("Failed to retrieve {0}".format(url))

    if python3:
        data = data.decode("utf-8")

    match = re.search(settings["firefox"]["pattern"], data)
    if not match:
        sys.exit("Failed to locate the download link for Firefox!")

    return match.group(0)


def retrieve_nodejs_download_url():
    url = settings["nodejs"]["url"]

    try:
        data = urllib.urlopen(url).read()
    except:
        sys.exit("Failed to retrieve {0}".format(url))

    if python3:
        data = data.decode("utf-8")

    match = re.search(settings["nodejs"]["pattern"], data)
    if not match:
        sys.exit("Failed to locate the download link for NodeJS!")

    return url + "/" + match.group(1)


def retrieve_git_download_url():
    url = settings["git"]["url"]

    try:
        data = urllib.urlopen(url).read()
    except:
        sys.exit("Failed to retrieve {0}".format(url))

    if python3:
        data = data.decode("utf-8")

    match = re.search(settings["git"]["pattern"], data)
    if not match:
        sys.exit("Failed to locate the download link for Git!")

    return match.group(0)


def download_and_install_browser(program, abortOnFail=True):
    filename = os.path.join(temporary_path, "{0}_setup".format(program))
    netfile = urllib.URLopener()

    if program == "chrome":
        url = settings["chrome"]["url"]

    elif program == "firefox":
        url = retrieve_firefox_download_url()

    elif program == "nodejs":
        url = retrieve_nodejs_download_url()

    elif program == "git":
        url = retrieve_git_download_url()

    elif program == "graphicsmagick":
        url = settings["graphicsmagick"]["url"]

    else:
        sys.exit("Unknown browser '{0}'! Allowed values: chrome, firefox, nodejs, git".format(program))

    extension = url[-4:]
    if not "." in extension:
        extension = ".exe"
    filename += extension  # Adds .exe, .msi or similar to the file ending from URL.

    sys.stdout.write("Downloading {0}... ".format(program))
    sys.stdout.flush()
    try:
        netfile.retrieve(urllib.urlopen(url).geturl(), filename)
        print("Done!")
    except:
        sys.exit("Failed to download {0} to {1}".format(url, filename))

    if extension == ".msi":
        print("PLEASE NOTE: If the following installation gets stuck, please press <any key> to make it wake up.")
        filename = "msiexec.exe /i {0} /quiet".format(filename)

    sys.stdout.write("Installing {0}... ".format(program))
    sys.stdout.flush()
    process = subprocess.Popen(
        filename + " " + settings[program]["install_arguments"]
    )

    process.communicate()
    if process.returncode != 0 and abortOnFail:
        sys.exit("Failed!")

    print("Success!")

perform_registry_changes()
download_and_install_browser("chrome", abortOnFail=False)

download_and_install_browser("firefox", abortOnFail=False)
disable_import_wizard_for_firefox()

download_and_install_browser("git", abortOnFail=False)
download_and_install_browser("nodejs", abortOnFail=False)
download_and_install_browser("graphicsmagick")