#!/usr/bin/python3

import json
import sys
import os
import re
import shutil
import pathlib
from terminal import eprint, status_print, warning_print, success_print, confirm_prompt, default_print
from downloads import get_file_name_from_url, download_file
from pathlib import Path
from utils import which

VERSION = "v1.0.0"
PACKAGES_FILE = "packages_list.json"
SUPPORTED_PACKAGE_MANAGERS_COMMANDS = {
    "apt": "sudo apt install",
    "pacman": "sudo pacman -Sy",
    "yay": "yay -Sy",
    "brew": "brew install"
}

SUPPORTED_PACKAGE_MANAGERS_SYSTEM_UPDATE = {
    "apt": [["sudo", "apt", "update"], ["sudo", "apt", "upgrade"]],
    "pacman": ["sudo", "pacman", "-Syu"],
    "yay": ["yay", "-Syu"],
    "brew": [["brew", "update"], ["brew", "upgrade"]]
}

SUPPORTED_VARIABLES = {
    "FONT_DIR": str(Path.home()) + "/Library/Fonts" if sys.platform == "darwin" else str(
        Path.home()) + "/.local/share/fonts",
    "LOCAL_BIN_DIR": str(Path.home()) + "/.local/bin",
    "HOME": str(Path.home())
}


def replace_variables(s: str):
    # regex: \%\(([^)]+)\)

    m = s

    for key in SUPPORTED_VARIABLES:
        m = re.sub(r"\%\(\b{}\b\)".format(key), SUPPORTED_VARIABLES[key], m)

    return m


class Options:
    def __init__(self, options_array):
        self.enabled_packages_array = []
        self.all_enabled = False
        self.disabled_packages_array = []
        self.verbose = False
        self.batch_mode = False
        self.dry_run = False
        self.skip_all = False

        i = 0
        while i < len(options_array):
            if options_array[i] == '--batch' or options_array[i] == '-b':
                self.batch_mode = True
                i += 1
            elif options_array[i] == '--verbose':
                self.verbose = True
                i += 1
            elif options_array[i] == '--enable-all':
                self.all_enabled = True
                i += 1
            elif options_array[i] == '--dry-run':
                self.dry_run = True
                i += 1
            elif options_array[i] == '--skip-all':
                self.skip_all = True
                i += 1
            elif options_array[i] == '--enable':
                i += 1

                if i >= len(options_array):
                    eprint("No package given to enable.")
                    exit(1)

                self.enabled_packages_array.append(options_array[i])
                i += 1
            elif options_array[i] == '--disable':
                i += 1

                if i >= len(options_array):
                    eprint("No package given to disable.")
                    exit(1)

                self.disabled_packages_array.append(options_array[i])
                i += 1
            else:
                eprint("Unknown flag: " + options_array[i])
                exit(1)

    def is_package_enabled(self, package):
        return (package.package_name() in self.enabled_packages_array or package.is_enabled() or self.all_enabled) and package.package_name() not in self.disabled_packages_array

    def enabled_packages(self, packages_list):
        packages = []

        for package in packages_list:
            if self.is_package_enabled(package):
                success_print("Enabling " + package.package_name())
                packages.append(package)
            elif self.verbose:
                warning_print("Disabling " + package.package_name())

        return packages


class Config:
    def __init__(self, source, dest=None, platform="all"):
        self.source = source
        self.dest = dest
        self.platform = platform

    def valid(self):
        if self.platform == "all":
            return True
        elif self.platform == "macos" and sys.platform == "darwin":
            return True
        elif self.platform == "linux" and sys.platform.startswith("linux"):
            return True
        else:
            return False

    def source_path(self):
        return self.source

    def destination_path(self):
        if self.dest is None:
            # Remove up to the directory where this script is running.
            dir_path = os.path.dirname(os.path.realpath(__file__))

            return self.source.replace(dir_path, str(Path.home()))
        else:
            return self.dest

    def make_dest_path(self, options: Options):
        pth = os.path.split(self.destination_path())[0]

        if os.path.exists(pth):
            if options.verbose:
                default_print("Path already exists: " + pth)
            return

        if options.verbose:
            default_print("Making path " + pth)

        if not options.dry_run:
            pathlib.Path(pth).mkdir(parents=True, exist_ok=True)

    def __str__(self):
        if self.dest is not None:
            return "Config (source: " + self.source + ", dest: " + self.dest + ")"
        else:
            return "Config (source: " + self.source + ")"

    def __repr__(self):
        return str(self)


class Package:
    def __init__(self, dictionary):
        if "name" not in dictionary or "supported-package-managers" not in dictionary:
            eprint("Error invalid package: " + str(dictionary) +
                   " " + str(type(dictionary)))
            exit(1)
        else:
            self.name = dictionary["name"]
            self.supported_package_managers = {}
            self.disabled = False
            self.configs = []
            self.install_cmds = []
            self.post_install_cmds = []
            self.url = None
            self.repo = None

            if "disabled" in dictionary:
                self.disabled = bool(dictionary["disabled"])

            if dictionary["supported-package-managers"] is not None:
                for pm in dictionary["supported-package-managers"]:
                    if "name_" + pm in dictionary:
                        self.supported_package_managers[pm] = dictionary["name_"+pm]
                    else:
                        self.supported_package_managers[pm] = self.name

            if "configs" in dictionary:
                for config in dictionary["configs"]:
                    if "source" not in config:
                        eprint(
                            "No 'source' key in the 'config' section for " + self.name)
                        exit(1)

                    source = replace_variables(str(config["source"]))

                    if "dest" in config:
                        c = Config(source, dest=replace_variables(
                            str(config["dest"])))
                    else:
                        c = Config(source)

                    if c.valid():
                        self.configs.append(c)

            if "install-cmds" in dictionary:
                for cmd in dictionary["install-cmds"]:
                    self.install_cmds.append(replace_variables(cmd))

            if "post-install-cmds" in dictionary:
                for cmd in dictionary["post-install-cmds"]:
                    self.post_install_cmds.append(replace_variables(cmd))

            if "url" in dictionary:
                self.url = dictionary["url"]

            if "repo" in dictionary:
                self.repo = dictionary["repo"]

    def package_name(self, manager=None):
        if manager is not None and manager in self.supported_package_managers:
            return self.supported_package_managers[manager]

        return self.name

    def is_enabled(self):
        return not self.disabled

    def install_configs(self, options: Options):
        for conf in self.configs:
            conf.make_dest_path(options)

            if options.verbose:
                default_print("Copying " + conf.source_path() +
                              " to " + conf.destination_path())

            if not options.dry_run:
                shutil.copy(conf.source_path(), conf.destination_path())

    def install(self, options: Options, manager=None):
        if which(self.name) is not None:
            def conf():
                warning_print("The binary " + self.name +
                              " has been detected on this system. Do you wish to skip this package? (y/n): ", end="")

            if options.skip_all or confirm_prompt(conf):
                warning_print("Skipping " + self.name)
                return False

        if manager is None:
            self.__install_with_url(options)
        elif manager not in self.supported_package_managers:
            if self.url is not None or self.repo is not None:
                def conf():
                    warning_print("The package " + self.name + " cannot be installed by " +
                                  manager + ". Do you wish to install this package using the provided URL/repo (y/n): ", end="")

                if confirm_prompt(conf):
                    self.__install_with_url(options)
                else:
                    warning_print("Skipping " + self.name)
                    return False
            else:
                def conf():
                    warning_print("The package " + self.name + " cannot be installed by " +
                                  manager + ". Do you wish to skip this package (y/n): ", end="")

                if confirm_prompt(conf):
                    warning_print("Skipping " + self.name)
                    return False
                else:
                    eprint("Failed to install " + self.name)
                    exit(1)
        else:
            self.__install_with_manager(options, manager)

        if len(self.post_install_cmds) > 0:
            status_print("Running post-install commands for " + self.name)

            for cmd in self.post_install_cmds:
                if not execute_system_cmd(cmd, options.dry_run):
                    exit(1)

        return True

    def __install_with_url(self, options: Options):
        if self.repo is not None:
            self.__git_clone(options.dry_run)
        else:
            self.__download(options.dry_run)

        status_print("Running install commands for " + self.name)

        for cmd in self.install_cmds:
            if not execute_system_cmd(cmd, options.dry_run):
                exit(1)

        return True

    def __git_clone(self, dry_run):
        if self.repo is None:
            eprint("No git repo URL provided for package " + self.name)
            exit(1)

        if dry_run:
            status_print("git clone " + self.repo)
        else:
            if os.system("git clone" + self.repo) != 0:
                eprint("Git clone failed for package " + self.name)
                exit(1)

    def __download(self, dry_run):
        if self.url is None:
            eprint("No URL provided for package " + self.name)
            exit(1)

        file_name = get_file_name_from_url(self.url)

        if dry_run:
            status_print("Download " + file_name + " from " + self.url + " ")
        else:
            download_file(self.url)

    def __install_with_manager(self, options: Options, manager):
        if manager is None:
            eprint("Failed attempt to install " +
                   self.name + ". No package manager.")
            exit(1)
        else:
            return execute_system_cmd(
                SUPPORTED_PACKAGE_MANAGERS_COMMANDS[manager] + " " + self.package_name(manager), options.dry_run)

    def __str__(self) -> str:
        return "Package {{\n\tname: {0}\n\tsupported_package_managers: {1}\n\tconfigs: {2}\n\tinstall_cmds: {3}\n\tpost_install_cmds: {4}\n\turl: {5}\n}}".format(self.name, self.supported_package_managers, self.configs, self.install_cmds, self.post_install_cmds, self.url)

    def __repr__(self) -> str:
        return str(self)


def main():
    if os.name == "nt":
        eprint("Windows is not supported.")
        exit(1)

    mode, options = process_cli_args()

    options = Options(options)

    manager = check_for_package_manager()

    if manager is None:
        eprint(
            "No package manager was found and most packages require a package manager.")
        exit(1)

    if options.verbose:
        for k in SUPPORTED_VARIABLES:
            default_print("Initializing variable " + k + " to " +
                          SUPPORTED_VARIABLES[k], bold=False)

    packages = load_packages_list()

    packages = options.enabled_packages(packages)

    if mode == "install":
        install_packages(packages, options, manager)
        install_configs(packages, options)
    elif mode == "install_packages":
        install_packages(packages, options, manager)
    elif mode == "install_configs":
        install_configs(packages, options)


def process_cli_args():
    mode = None
    options = list()
    i = 1

    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg == '-h' or arg == '--help':
            print("install.py [mode] [options]")

            print("\nModes")
            print(" install                \tInstall all packages and configs")
            print(" install_configs        \tInstall configs only")
            print(" install_packages       \tInstall packages only")
            print("\nOptions")
            print(" --help, -h             \tShow this message")
            print(" --version              \tShow version information")
            print(" --disable [package]    \tDisable a package")
            print(" --enable  [package]    \tEnable a package")
            print(" --enable-all           \tEnable all packages")
            print(" --dry-run              \tPrint commands but don't execute them.")
            print(" --skip-all             \tSkip any packages that are already installed but still install their configs.")
            print(
                " --batch                \tInstall all enabled packages with a single package manager command")
            print(" --verbose              \tEnable verbose printing")

            exit(0)
        elif arg == '--version':
            print(VERSION)
            exit(0)
        elif mode is None:
            if arg == "install" or arg == "install_configs" or arg == "install_packages":
                mode = arg
            else:
                eprint("Invalid mode: " + arg)
                exit(1)
            i += 1
        else:
            options.append(sys.argv[i])

            i += 1

    if mode is None:
        eprint("No mode chosen.")
        exit(1)

    return (mode, options)


def check_for_package_manager():
    found_manager = None

    for manager in SUPPORTED_PACKAGE_MANAGERS_COMMANDS:
        if which(manager):
            if found_manager is None:
                found_manager = manager
            else:
                opt = input("Two package managers have been found. \n1: " + found_manager +
                            "\n2: " + manager + "\nWhich manager do you want to use (1/2): ")

                if opt == "1":
                    pass
                elif opt == "2":
                    found_manager = manager
                else:
                    eprint("Invalid option: " + opt)
                    exit(1)

                warning_print("Using " + found_manager)

    return found_manager


def load_packages_list():
    f = open(PACKAGES_FILE, "r")
    packages = f.read()
    packages = json.loads(packages)

    packages_list = []

    for package in packages["packages"]:
        if "name" in package:
            packages_list += [Package(package)]
        else:
            eprint("Error invalid package: " + str(package) +
                   " " + str(type(package)))
            exit(1)

    return packages_list


def install_packages(packages, options: Options, manager=None):
    for package in packages:
        if package.install(options, manager):
            success_print("Successfully installed " +
                          package.package_name(manager))


def install_configs(packages, options: Options):
    for pkg in packages:
        status_print("Installing configs for " + pkg.name)
        pkg.install_configs(options)


def execute_system_cmd(cmd, dry_run):
    default_print("Executing '" + cmd + "'", bold=False)

    if not dry_run:
        code = os.system(cmd)

        if code != 0:
            eprint("Error: The return code was " + code + ", not 0.")
            return False

    return True


if __name__ == "__main__":
    main()
