#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package of `go.mod` parser."""

import re


class ModuleReference:
    """A class used to represent a tuple of module and version.

    Attributes
    ----------
    module : str
        the name of golang module
    version : str
        the version of golang module, conforming to semver rules

    """

    def __init__(self, module, version):
        """Create a instance of `ModuleReference` object.

        Parameters
        ----------
        module : str
            the name of golang module
        version : str
            the version of golang module, conforming to semver rules
        """
        self._module = module
        self._version = version

    @property
    def module(self):
        """Return module."""
        return self._module

    @property
    def version(self):
        """Return version."""
        return self._version

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"mod: {self.module}, version: {self.version}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"{self.module} {self.version}"


class Require(ModuleReference):
    """A class used to represent a `require` directive in go.mod.

    Attributes
    ----------
    indirect : bool
        Whether this dependency is a direct or indirect one

    """

    def __init__(self, module, version, indirect):
        """Create a instance of `Require` object.

        Parameters
        ----------
        module : str
            the name of golang module
        version : str
            the version of golang module, conforming to semver rules
        indirect : bool
            Whether this dependency is a direct or indirect one
        """
        super().__init__(module, version)
        self._indirect = indirect

    @property
    def indirect(self):
        """Return indirect."""
        return self._indirect

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"{super().__repr__()}, indirect: {self.indirect}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"{super().__str__()}{' //indirect' if self.indirect else ''}"


class Replace:
    """A class used to represent a `replace` directive in go.mod.

    Attributes
    ----------
    left : ModuleReference
        the source module and optional version to be replaced
    right : ModuleReference
        the replacement module and optional version

    """

    def __init__(self, left, right):
        """Create a instance of `Replace` object.

        Parameters
        ----------
        left : ModuleReference
            the source module and optional version to be replaced
        right : ModuleReference
            the replacement module and optional version
        """
        self._left = left
        self._right = right

    @property
    def left(self):
        """Return module to be replaced."""
        return self._left

    @property
    def right(self):
        """Return replacement."""
        return self._right

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"{self.left.__repr__()} => {self.right.__repr__()}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"{self.left.__str__()} => {self.right.__str__()}"


class Retract:
    """A class used to represent a `retract` directive in go.mod.

    Attributes
    ----------
    versions : list of str
        the list of versions, conforming to semver, to retract

    """

    def __init__(self, versions):
        """Create an instance of `Retract` object.

        Parameters
        ----------
        versions : list of str
            the list of versions, conforming to semver, to retract
        """
        self._versions = versions

    @property
    def versions(self):
        """Return list of str representing semver versions."""
        return self._versions

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        return f"{[v for v in self.versions]}"

    def __str__(self):
        """Represnt this object as a string."""
        return f"{[v for v in self.versions]}"


class GoMod:
    """A class used to represent a `go.mod` file.

    Attributes
    ----------
    module_path : str
        the defined golang module path to which other module reference
    go_version : str
        the version of golang required by this module
    toolchain : str
        the golang toolchain required by this module
    requires : list of Require
        dependencies of this module, list of Require objects
    replaces : list of Require
        list of module replacements, list of Replace objects
    retract : list of str
        list of module replacements, list of str
    """

    ModulePathDirectivePat = re.compile(r"module\s+(.*)")
    GoVersionDirectivePat = re.compile(r"go\s+(.*)")
    ToolchainDirectivePat = re.compile(r"tailchain\s+(.*)")
    RequireDirectivePat1 = re.compile(r"^\s*require\s+(.*?)\s+(v.+)$", re.MULTILINE)  # noqa: E501
    RequireDirectivePat2 = re.compile(r"require\s+\(\s*\n\s*(?:.*\s+v.+\n)+\)")  # noqa: E501
    RequireDirectivePat21 = re.compile(r"^\s*(\w+(?:.*?))\s+(v.+)$", re.MULTILINE)  # noqa: E501
    ReplaceDirectivePat1 = re.compile(r"replace\s+(\w+(?:.*?))\s+(v.+)?\s*=>\s*((?:\.|/|-|\w)+)\s*(v.+)?")  # noqa: E501
    ReplaceDirectivePat2 = re.compile(r"replace\s+\(\s*\n\s*(?:.*\n)+\)")
    ReplaceDirectivePat21 = re.compile(r"^\s*(\w+(?:.*?))\s+(v.+)?\s*=>\s*((?:\.|/|-|\w)+)\s*(v.+)?$", re.MULTILINE)  # noqa: E501
    RetractDirectivePat1 = re.compile(r"retract\s+(v.+)")
    RetractDirectivePat2 = re.compile(r"retract\s+(v.+(?:v.+,)*)")

    def __init__(self, content):
        """Create an instance of `GoMod` object by parsing `content`.

        This constructor parses the `go.mod` content into an instance of
        `GoMod` object.

        Parameters
        ----------
        content : str
            the content of `go.mod` file
        """
        self._module_path = ""
        self._go_version = ""
        self._toolchain = ""
        self._excludes = []
        self._retract = []

        self._parse(content)

    def _parse(self, content):
        # strip pure comment lines

        lines = content.split("\n")
        content = "\n".join(
            [line for line in lines if not re.match(r"^\s*//.*", line)]
        )

        m = re.search(GoMod.ModulePathDirectivePat, content)
        if m:
            self._module_path = m.group(1)

        m = re.search(GoMod.GoVersionDirectivePat, content)
        if m:
            self._go_version = m.group(1)

        m = re.search(GoMod.ToolchainDirectivePat, content)
        if m:
            self._toolchain = m.group(1)

        requires = []
        # parse module dependency
        for m in re.finditer(GoMod.RequireDirectivePat1, content):
            requires.append(self._parse_require(m.group(1), m.group(2)))

        for m1 in re.finditer(GoMod.RequireDirectivePat2, content):
            for m2 in re.finditer(GoMod.RequireDirectivePat21, m1.group(0)):
                requires.append(self._parse_require(m2.group(1), m2.group(2)))
        self._requires = requires

        # parse replace
        replaces = []
        # parse module dependency
        for m in re.finditer(GoMod.ReplaceDirectivePat1, content):
            replaces.append(self._parse_replace(*m.groups()))

        for m1 in re.finditer(GoMod.ReplaceDirectivePat2, content):
            for m2 in re.finditer(GoMod.ReplaceDirectivePat21, m1.group(0)):
                replaces.append(self._parse_replace(*m2.groups()))
        self._replaces = replaces

    def _parse_require(self, module, version_str):
        indirect = False
        version = ""
        if version_str.find("//") > 0:
            ver, comment = version_str.split('//', 1)
            indirect = comment.find("indirect") > 0
            version = ver.lstrip().rstrip()
        else:
            version = version_str.lstrip().rstrip()

        return Require(module, version, indirect)

    def _parse_replace(self, left_mod, left_ver, right_mod, right_ver):
        if left_ver is None:
            left_ver = ''
        if right_ver is None:
            right_ver = ''

        return Replace(
            ModuleReference(left_mod, left_ver),
            ModuleReference(right_mod, right_ver),
        )

    @property
    def module_path(self):
        """Return module path."""
        return self._module_path

    @property
    def go_version(self):
        """Return go version."""
        return self._go_version

    @property
    def toolchain(self):
        """Return go toolchain."""
        return self._toolchain

    @property
    def requires(self):
        """Return required dependencies."""
        return self._requires

    @property
    def excludes(self):
        """Return excludes."""
        return self._excludes

    @property
    def replaces(self):
        """Return replaces."""
        return self._replaces

    @property
    def retract(self):
        """Return retract."""
        return self._retract

    def __repr__(self):
        """Represnt this object as a string for debug purpose."""
        requires = "\n".join([req.__repr__() for req in self.requires])
        return "mod-path: %s go-ver: %s tc: %s \n %s \n %s \n%s \n%s" % (
            self.module_path,
            self.go_version,
            self.toolchain,
            requires,
            self.excludes,
            self.replaces,
            self.retract,
        )

    def __str__(self):
        """Represnt this object as a string."""
        requires = "\n".join([req.__str__() for req in self.requires])
        replaces = "\n".join([req.__str__() for req in self.replaces])
        return "%s %s\n%s\n%s\n%s\n%s" % (
            self.module_path,
            self.go_version,
            requires,
            self.excludes,
            replaces,
            self.retract
        )
