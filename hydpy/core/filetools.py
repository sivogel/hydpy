# -*- coding: utf-8 -*-
"""This module provides features for handling the folder structure of *HydPy*  projects
as well as loading data from and storing data to files."""
# import...
# ...from standard library
from __future__ import annotations
import contextlib
import os
import runpy
import shutil
import zipfile
import types
from typing import *

# ...from site-packages
import numpy

# ...from HydPy
import hydpy
from hydpy import config
from hydpy.core import exceptiontools
from hydpy.core import devicetools
from hydpy.core import netcdftools
from hydpy.core import objecttools
from hydpy.core import optiontools
from hydpy.core import propertytools
from hydpy.core import selectiontools
from hydpy.core import sequencetools
from hydpy.core import timetools
from hydpy.core.typingtools import *


class Folder2Path:
    """Map folder names to their pathnames.

    You can both pass positional arguments and keyword arguments when initialising
    |Folder2Path|.  For positional arguments, the folder and its path are assumed to be
    identical.  For keyword arguments, the keyword corresponds to the folder name and
    its value to the pathname:

    >>> from hydpy.core.filetools import Folder2Path
    >>> Folder2Path()
    Folder2Path()
    >>> f2p = Folder2Path(
    ...     "folder1", "folder2", folder3="folder3", folder4="path4")
    >>> f2p
    Folder2Path(folder1,
                folder2,
                folder3,
                folder4=path4)
    >>> print(f2p)
    Folder2Path(folder1, folder2, folder3, folder4=path4)

    To add folders after initialisation is supported:

    >>> f2p.add("folder5")
    >>> f2p.add("folder6", "path6")
    >>> f2p
    Folder2Path(folder1,
                folder2,
                folder3,
                folder5,
                folder4=path4,
                folder6=path6)

    Folder names are required to be valid Python identifiers:

    >>> f2p.add("folder 7")
    Traceback (most recent call last):
    ...
    ValueError: The given name string `folder 7` does not define a valid variable \
identifier.  Valid identifiers do not contain characters like `-` or empty spaces, do \
not start with numbers, cannot be mistaken with Python built-ins like `for`...)

    You can query the folder and attribute names:

    >>> f2p.folders
    ['folder1', 'folder2', 'folder3', 'folder4', 'folder5', 'folder6']
    >>> f2p.paths
    ['folder1', 'folder2', 'folder3', 'path4', 'folder5', 'path6']

    Attribute access and iteration are also supported:

    >>> "folder1" in dir(f2p)
    True
    >>> f2p.folder1
    'folder1'
    >>> f2p.folder4
    'path4'

    >>> for folder, path in f2p:
    ...     print(folder, path)
    folder1 folder1
    folder2 folder2
    folder3 folder3
    folder4 path4
    folder5 folder5
    folder6 path6

    >>> len(f2p)
    6
    >>> bool(f2p)
    True
    >>> bool(Folder2Path())
    False
    """

    def __init__(self, *args: str, **kwargs: str) -> None:
        for arg in args:
            self.add(arg)
        for (key, value) in kwargs.items():
            self.add(key, value)

    def add(self, directory: str, path: Optional[str] = None) -> None:
        """Add a directory and optionally its path."""
        objecttools.valid_variable_identifier(directory)
        if path is None:
            path = directory
        setattr(self, directory, path)

    @property
    def folders(self) -> List[str]:
        """The currently handled folder names."""
        return [folder for folder, path in self]

    @property
    def paths(self) -> List[str]:
        """The currently handled path names."""
        return [path for folder, path in self]

    def __iter__(self) -> Iterator[Tuple[str, str]]:
        for key, value in sorted(vars(self).items()):
            yield key, value

    def __len__(self) -> int:
        return len(vars(self))

    def __str__(self) -> str:
        return " ".join(repr(self).split())

    def __repr__(self) -> str:
        if self:
            args, kwargs = [], []
            for key, value in self:
                if key == value:
                    args.append(key)
                else:
                    kwargs.append(f"{key}={objecttools.repr_(value)}")
            lines = [f"            {arg}," for arg in args + kwargs]
            lines[0] = "Folder2Path(" + lines[0][12:]
            lines[-1] = lines[-1][:-1] + ")"
            return "\n".join(lines)
        return "Folder2Path()"


class FileManager:
    """Base class for |NetworkManager|, |ControlManager|, |ConditionManager|, and
    |SequenceManager|."""

    BASEDIR: str
    DEFAULTDIR: Optional[str]

    _projectdir: Optional[str]
    _currentdir: Optional[str]

    def __init__(self) -> None:
        self._projectdir = None
        try:
            self.projectdir = hydpy.pub.projectname
        except RuntimeError:
            pass
        self._currentdir = None

    def _get_projectdir(self) -> str:
        """The name of the main folder of a project.

        For the `LahnH` example project, |FileManager.projectdir| is (not surprisingly)
        `LahnH` and is queried from the |pub| module.  However, you can define or
        change |FileManager.projectdir| interactively, which can be useful for more
        complex tasks like copying (parts of) projects:

        >>> from hydpy.core.filetools import FileManager
        >>> from hydpy import pub
        >>> pub.projectname = "project_A"
        >>> filemanager = FileManager()
        >>> filemanager.projectdir
        'project_A'

        >>> del filemanager.projectdir
        >>> filemanager.projectdir
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `projectdir` of object \
`filemanager` has not been prepared so far.
        >>> filemanager.projectdir = "project_B"
        >>> filemanager.projectdir
        'project_B'

        >>> del pub.projectname
        >>> FileManager().projectdir
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: Attribute `projectdir` of object \
`filemanager` has not been prepared so far.
        """
        return self._projectdir  # type: ignore[return-value]

    def _set_projectdir(self, name: str) -> None:
        self._projectdir = name

    def _del_projectdir(self) -> None:
        self._projectdir = None

    projectdir = propertytools.ProtectedPropertyStr(
        _get_projectdir, _set_projectdir, _del_projectdir
    )

    @property
    def basepath(self) -> str:
        """The absolute path pointing to the available working directories.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.projectdir = "projectname"
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     repr_(filemanager.basepath)   # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename'
        """
        return os.path.abspath(os.path.join(self.projectdir, self.BASEDIR))

    @property
    def availabledirs(self) -> Folder2Path:
        """The names and paths of the available working directories.

        All possible working directories must be availablein the base directory of the
        respective |FileManager| subclass.  Folders with names starting with an
        underscore do not count (use this for directories handling additional data
        files, if you like), while zipped directories do count as available directories:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.projectdir = "projectname"
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> with TestIO():
        ...     os.makedirs("projectname/basename/folder1")
        ...     os.makedirs("projectname/basename/folder2")
        ...     open("projectname/basename/folder3.zip", "w").close()
        ...     os.makedirs("projectname/basename/_folder4")
        ...     open("projectname/basename/folder5.tar", "w").close()
        ...     filemanager.availabledirs   # doctest: +ELLIPSIS
        Folder2Path(folder1=.../projectname/basename/folder1,
                    folder2=.../projectname/basename/folder2,
                    folder3=.../projectname/basename/folder3.zip)
        """
        directories = Folder2Path()
        for directory in sorted(os.listdir(self.basepath)):
            if not directory.startswith("_"):
                path = os.path.join(self.basepath, directory)
                if os.path.isdir(path):
                    directories.add(directory, path)
                elif directory.endswith(".zip"):
                    directories.add(directory[:-4], path)
        return directories

    @property
    def currentdir(self) -> str:
        """The name of the current working directory containing the relevant files.

        To show most of the functionality of |property| |FileManager.currentdir| (we
        explain unpacking zipped files on the fly in the documentation on function
        |FileManager.zip_currentdir|), we first prepare a |FileManager| object with the
        default |FileManager.basepath| `projectname/basename`:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.DEFAULTDIR = None
        >>> filemanager.projectdir = "projectname"
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> with TestIO():
        ...     os.makedirs("projectname/basename")
        ...     repr_(filemanager.basepath)  # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename'

        At first, the base directory is empty and asking for the current working
        directory results in the following error:

        >>> with TestIO():
        ...     filemanager.currentdir  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object has not \
been defined manually and cannot be determined automatically: \
`.../projectname/basename` does not contain any available directories.

        If only one directory exists, it is considered as the current working directory
        automatically:

        >>> with TestIO():
        ...     os.mkdir("projectname/basename/dir1")
        ...     filemanager.currentdir
        'dir1'

        |property| |FileManager.currentdir| memorises the name of the current working
        directory, even if another directory is added later to the base path:

        >>> with TestIO():
        ...     os.mkdir("projectname/basename/dir2")
        ...     filemanager.currentdir
        'dir1'

        Set the value of |FileManager.currentdir| to |None| to let it forget the
        memorised directory.  After that, to try to query the current working directory
        results in another error, as it is not clear which directory to select:

        >>> with TestIO():
        ...     filemanager.currentdir = None
        ...     filemanager.currentdir  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object has not \
been defined manually and cannot be determined automatically: \
`....../projectname/basename` does contain multiple available directories (dir1 and \
dir2).

        Setting |FileManager.currentdir| manually solves the problem:

        >>> with TestIO():
        ...     filemanager.currentdir = "dir1"
        ...     filemanager.currentdir
        'dir1'

        Remove the current working directory `dir1` with the `del` statement:

        >>> with TestIO():
        ...     del filemanager.currentdir
        ...     os.path.exists("projectname/basename/dir1")
        False

        |FileManager| subclasses can define a default directory name.  When many
        directories exist, and none is selected manually, the default directory is
        selected automatically.  The following example shows an error message due to
        multiple directories without any having the default name:

        >>> with TestIO():
        ...     os.mkdir("projectname/basename/dir1")
        ...     filemanager.DEFAULTDIR = "dir3"
        ...     del filemanager.currentdir
        ...     filemanager.currentdir  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        RuntimeError: The current working directory of the FileManager object has not \
been defined manually and cannot be determined automatically: The default directory \
(dir3) is not among the available directories (dir1 and dir2).

        We can fix this by adding the required default directory manually:

        >>> with TestIO():
        ...     os.mkdir("projectname/basename/dir3")
        ...     filemanager.currentdir
        'dir3'

        Setting the |FileManager.currentdir| to `dir4` not only overwrites the default
        name but also creates the required folder:

        >>> with TestIO():
        ...     filemanager.currentdir = "dir4"
        ...     filemanager.currentdir
        'dir4'
        >>> with TestIO():
        ...     sorted(os.listdir("projectname/basename"))
        ['dir1', 'dir2', 'dir3', 'dir4']

        Failed attempts to remove directories result in error messages like the
        following one:

        >>> import shutil
        >>> from unittest.mock import patch
        >>> with patch.object(shutil, "rmtree", side_effect=AttributeError):
        ...     with TestIO():
        ...         del filemanager.currentdir  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError: While trying to delete the current working directory \
`.../projectname/basename/dir4` of the FileManager object, the following error \
occurred: ...

        Then, the current working directory still exists and is remembered by property
        |FileManager.currentdir|:

        >>> with TestIO():
        ...     filemanager.currentdir
        'dir4'
        >>> with TestIO():
        ...     sorted(os.listdir("projectname/basename"))
        ['dir1', 'dir2', 'dir3', 'dir4']

        Assign the folder's absolute path if you need to work outside the current
        project directory (for example, to archive simulated data):

        >>> with TestIO():  # doctest: +ELLIPSIS
        ...     os.mkdir("differentproject")
        ...     filemanager.currentdir = os.path.abspath("differentproject/dir1")
        ...     repr_(filemanager.currentpath)
        ...     os.listdir("differentproject")
        '...hydpy/tests/iotesting/differentproject/dir1'
        ['dir1']
        """
        currentdir = self._currentdir
        if currentdir is None:
            directories = self.availabledirs.folders
            if len(directories) == 1:
                currentdir = directories[0]
            elif self.DEFAULTDIR in directories:
                currentdir = self.DEFAULTDIR
            else:
                prefix = (
                    f"The current working directory of the {type(self).__name__} "
                    f"object has not been defined manually and cannot be determined "
                    f"automatically:"
                )
                if not directories:
                    raise RuntimeError(
                        f"{prefix} `{objecttools.repr_(self.basepath)}` does not "
                        f"contain any available directories."
                    )
                if self.DEFAULTDIR is None:
                    raise RuntimeError(
                        f"{prefix} `{objecttools.repr_(self.basepath)}` does contain "
                        f"multiple available directories "
                        f"({objecttools.enumeration(directories)})."
                    )
                raise RuntimeError(
                    f"{prefix} The default directory ({self.DEFAULTDIR}) is not among "
                    f"the available directories "
                    f"({objecttools.enumeration(directories)})."
                )
            self.currentdir = currentdir
        return currentdir

    @currentdir.setter
    def currentdir(self, directory: Optional[str]) -> None:
        if directory is None:
            self._currentdir = None
        else:
            dirpath = os.path.join(self.basepath, directory)
            zippath = f"{dirpath}.zip"
            if os.path.exists(zippath):
                shutil.unpack_archive(
                    filename=zippath,
                    extract_dir=os.path.join(self.basepath, directory),
                    format="zip",
                )
                os.remove(zippath)
            elif not os.path.exists(dirpath):
                os.makedirs(dirpath)
            self._currentdir = str(directory)

    @currentdir.deleter
    def currentdir(self) -> None:
        path = os.path.join(self.basepath, self.currentdir)
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to delete the current working directory "
                    f"`{objecttools.repr_(path)}` of the {type(self).__name__} object"
                )
        self._currentdir = None

    @property
    def currentpath(self) -> str:
        """The absolute path of the current working directory.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.projectdir = "projectname"
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = "testdir"
        ...     repr_(filemanager.currentpath)    # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename/testdir'
        """
        return os.path.join(self.basepath, self.currentdir)

    @property
    def filenames(self) -> List[str]:
        """The names of the files placed in the current working directory, except those
        starting with an underscore.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.projectdir = "projectname"
        >>> from hydpy import TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = "testdir"
        ...     open("projectname/basename/testdir/file1.txt", "w").close()
        ...     open("projectname/basename/testdir/file2.npy", "w").close()
        ...     open("projectname/basename/testdir/_file1.nc", "w").close()
        ...     filemanager.filenames
        ['file1.txt', 'file2.npy']
        """
        return sorted(
            fn for fn in os.listdir(self.currentpath) if not fn.startswith("_")
        )

    @property
    def filepaths(self) -> List[str]:
        """The absolute path names of the files returned by property
        |FileManager.filenames|.

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.projectdir = "projectname"
        >>> from hydpy import repr_, TestIO
        >>> with TestIO():
        ...     filemanager.currentdir = "testdir"
        ...     open("projectname/basename/testdir/file1.txt", "w").close()
        ...     open("projectname/basename/testdir/file2.npy", "w").close()
        ...     open("projectname/basename/testdir/_file1.nc", "w").close()
        ...     for filepath in filemanager.filepaths:
        ...         repr_(filepath)    # doctest: +ELLIPSIS
        '...hydpy/tests/iotesting/projectname/basename/testdir/file1.txt'
        '...hydpy/tests/iotesting/projectname/basename/testdir/file2.npy'
        """
        path = self.currentpath
        return [os.path.join(path, name) for name in self.filenames]

    def zip_currentdir(self) -> None:
        """Pack the current working directory in a `zip` file.

        |FileManager| subclasses allow for manual packing and automatic unpacking of
        working directories.  The only supported format is "zip".  The original
        directories and zip files are removed after packing or unpacking, respectively,
        to avoid possible inconsistencies.

        As an example scenario, we prepare a |FileManager| object with the current
        working directory `folder` containing the files `test1.txt` and `text2.txt`:

        >>> from hydpy.core.filetools import FileManager
        >>> filemanager = FileManager()
        >>> filemanager.BASEDIR = "basename"
        >>> filemanager.DEFAULTDIR = None
        >>> filemanager.projectdir = "projectname"
        >>> import os
        >>> from hydpy import repr_, TestIO
        >>> TestIO.clear()
        >>> basepath = "projectname/basename"
        >>> with TestIO():
        ...     os.makedirs(basepath)
        ...     filemanager.currentdir = "folder"
        ...     open(f"{basepath}/folder/file1.txt", "w").close()
        ...     open(f"{basepath}/folder/file2.txt", "w").close()
        ...     filemanager.filenames
        ['file1.txt', 'file2.txt']

        The directories existing under the base path are identical to the ones returned
        by property |FileManager.availabledirs|:

        >>> with TestIO():
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs    # doctest: +ELLIPSIS
        ['folder']
        Folder2Path(folder=.../projectname/basename/folder)

        After packing the current working directory manually, it still counts as an
        available directory:

        >>> with TestIO():
        ...     filemanager.zip_currentdir()
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs    # doctest: +ELLIPSIS
        ['folder.zip']
        Folder2Path(folder=.../projectname/basename/folder.zip)

        Instead of the complete directory, only the contained files are packed:

        >>> from zipfile import ZipFile
        >>> with TestIO():
        ...     with ZipFile("projectname/basename/folder.zip", "r") as zp:
        ...         sorted(zp.namelist())
        ['file1.txt', 'file2.txt']

        The zip file is unpacked again as soon as `folder` becomes the current working
        directory:

        >>> with TestIO():
        ...     filemanager.currentdir = "folder"
        ...     sorted(os.listdir(basepath))
        ...     filemanager.availabledirs
        ...     filemanager.filenames    # doctest: +ELLIPSIS
        ['folder']
        Folder2Path(folder=.../projectname/basename/folder)
        ['file1.txt', 'file2.txt']
        """
        with zipfile.ZipFile(f"{self.currentpath}.zip", "w") as zipfile_:
            for filepath, filename in zip(self.filepaths, self.filenames):
                zipfile_.write(filename=filepath, arcname=filename)
        del self.currentdir


class NetworkManager(FileManager):
    """Manager for network files.

    The base and default folder names of class |NetworkManager| are:

    >>> from hydpy.core.filetools import NetworkManager
    >>> NetworkManager.BASEDIR
    'network'
    >>> NetworkManager.DEFAULTDIR
    'default'

    The documentation of base class |FileManager| explains most aspects of using
    |NetworkManager| objects.  The following examples deal with the extended features
    of class |NetworkManager|: reading, writing, and removing network files.  For this
    purpose, we prepare the example project `LahnH` in the `iotesting` directory by
    calling function |prepare_full_example_1|:

    >>> from hydpy.examples import prepare_full_example_1
    >>> prepare_full_example_1()

    You can define the complete network structure of an `HydPy` project by an arbitrary
    number of "network files".  These are valid Python files which define certain |Node|
    and |Element| as well as their connections.  Network files are allowed to overlap,
    meaning two or more files can define the same objects (in a consistent manner only,
    of course).  The primary purpose of class |NetworkManager| is to execute each
    network file individually and pass its content to a |Selection| object, which is
    done by method |NetworkManager.load_files|:

    >>> networkmanager = NetworkManager()
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     networkmanager.projectdir = "LahnH"
    ...     selections = networkmanager.load_files()

    Method |NetworkManager.load_files| takes file names as selection names (without
    file endings).  Additionally, it creates a "complete" selection, including the
    whole set of |Node| and |Element| objects of the file-specific selections:

    >>> selections
    Selections("complete", "headwaters", "nonheadwaters", "streams")
    >>> selections.headwaters
    Selection("headwaters",
              nodes=("dill", "lahn_1"),
              elements=("land_dill", "land_lahn_1"))
    >>> selections.complete
    Selection("complete",
              nodes=("dill", "lahn_1", "lahn_2", "lahn_3"),
              elements=("land_dill", "land_lahn_1", "land_lahn_2",
                        "land_lahn_3", "stream_dill_lahn_2",
                        "stream_lahn_1_lahn_2", "stream_lahn_2_lahn_3"))

    Method |NetworkManager.save_files| writes all |Selection| objects into separate
    files.  We first change the current working directory to ensure we do not overwrite
    already existing files:

    >>> import os
    >>> with TestIO():
    ...     networkmanager.currentdir = "testdir"
    ...     networkmanager.save_files(selections)
    ...     sorted(os.listdir("LahnH/network/testdir"))
    ['headwaters.py', 'nonheadwaters.py', 'streams.py']

    Reloading and comparing with the still available |Selection| objects proves that
    the contents of the original and the new network files are equivalent:

    >>> with TestIO():
    ...     selections == networkmanager.load_files()
    True

    Method |NetworkManager.delete_files| removes the network files of the given
    |Selection| objects:

    >>> selections -= selections.streams
    >>> with TestIO():
    ...     networkmanager.delete_files(selections)
    ...     sorted(os.listdir("LahnH/network/testdir"))
    ['streams.py']

    When defining network files, many things can go wrong.  In the following, we list
    all specialised error messages of what we hope to be concrete enough to aid in
    finding the relevant problems:

    >>> with TestIO():
    ...     networkmanager.delete_files(["headwaters"])   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to remove the network files of selections \
`['headwaters']`, the following error occurred: ...

    >>> with TestIO():
    ...     with open("LahnH/network/testdir/streams.py", "w") as wrongfile:
    ...         _ = wrongfile.write("x = y")
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    NameError: While trying to load the network file `...streams.py`, the following \
error occurred: name 'y' is not defined

    >>> with TestIO():
    ...     with open("LahnH/network/testdir/streams.py", "w") as wrongfile:
    ...         _ = wrongfile.write("from hydpy import Node")
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: The class Element cannot be loaded from the network file \
`...streams.py`.

    >>> with TestIO():
    ...     with open("LahnH/network/testdir/streams.py", "w") as wrongfile:
    ...         _ = wrongfile.write("from hydpy import Element")
    ...     networkmanager.load_files()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    RuntimeError: The class Node cannot be loaded from the network file `...streams.py`.

    >>> import shutil
    >>> with TestIO():
    ...     shutil.rmtree("LahnH/network/testdir")
    ...     networkmanager.save_files(selections)   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    FileNotFoundError: While trying to save the selections `Selections("complete", \
"headwaters", "nonheadwaters")` into network files, the following error occurred: ...
    """

    BASEDIR = "network"
    DEFAULTDIR = "default"

    def load_files(self) -> selectiontools.Selections:
        """Read all network files of the current working directory, structure their
        contents in a |selectiontools.Selections| object, and return it.

        See the main documentation on class |NetworkManager| for further information.
        """
        devicetools.Node.clear_all()
        devicetools.Element.clear_all()
        selections = selectiontools.Selections()
        if not self.filenames:
            raise RuntimeError(
                f"The directory `{self.currentpath}` does not contain any network "
                f"files."
            )
        for (filename, path) in zip(self.filenames, self.filepaths):
            # Ensure both `Node` and `Element`start with a `fresh` memory.
            devicetools.Node.extract_new()
            devicetools.Element.extract_new()
            try:
                info = runpy.run_path(path)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to load the network file `{path}`"
                )
            try:
                node: devicetools.Node = info["Node"]
                element: devicetools.Element = info["Element"]
                selections += selectiontools.Selection(
                    filename.split(".")[0], node.extract_new(), element.extract_new()
                )
            except KeyError as exc:
                raise RuntimeError(
                    f"The class {exc.args[0]} cannot be loaded from the network file "
                    f"`{path}`."
                ) from None
        selections += selectiontools.Selection(
            "complete", info["Node"].query_all(), info["Element"].query_all()
        )
        return selections

    def save_files(self, selections: Iterable[selectiontools.Selection]) -> None:
        """Save the |Selection| objects contained in the given |Selections| instance to
        separate network files.

        See the main documentation on class |NetworkManager| for further information.
        """
        try:
            currentpath = self.currentpath
            for selection in selections:
                if selection.name == "complete":
                    continue
                path = os.path.join(currentpath, selection.name + ".py")
                selection.save_networkfile(filepath=path)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the selections `{selections}` "
                f"into network files"
            )

    def delete_files(self, selections: Iterable[selectiontools.Selection]) -> None:
        """Delete the network files corresponding to the given selections (e.g. a
        |list| of |str| objects or a |Selections| object).

        See the main documentation on class |NetworkManager| for further information.
        """
        try:
            currentpath = self.currentpath
            for selection in selections:
                name = str(selection)
                if name == "complete":
                    continue
                if not name.endswith(".py"):
                    name += ".py"
                path = os.path.join(currentpath, name)
                os.remove(path)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to remove the network files of selections `{selections}`"
            )


class ControlManager(FileManager):
    """Manager for control parameter files.

    The base and default folder names of class |ControlManager| are:

    >>> from hydpy.core.filetools import ControlManager
    >>> ControlManager.BASEDIR
    'control'
    >>> ControlManager.DEFAULTDIR
    'default'

    Class |ControlManager| extends the functionalities of class |FileManager| only
    slightly, which is why the documentation on class |FileManager| should serve as a
    good starting point for understanding class |ControlManager|.  Also, see the
    documentation on method |HydPy.prepare_models| of class |HydPy|, which relies on
    the functionalities of class |ControlManager|.
    """

    # The following file path to content mapping is used to circumvent reading
    # the same auxiliary control parameter file from disk multiple times.
    _registry: Dict[str, types.CodeType] = {}
    _workingpath: str = "."
    BASEDIR = "control"
    DEFAULTDIR = "default"

    def load_file(
        self,
        element: Optional[devicetools.Element] = None,
        filename: Optional[str] = None,
        clear_registry: bool = True,
    ) -> Dict[str, Any]:
        """Return the namespace of the given file (and eventually of its corresponding
        auxiliary subfiles).

        By default, |ControlManager| clears the internal registry when after having
        loaded a control file and all its corresponding auxiliary files.  You can
        change this behaviour by passing `False` to the `clear_registry` argument,
        which might decrease model initialisation times significantly.  However, then
        it is your own responsibility to call the method |ControlManager.clear_registry|
        when necessary (usually before reloading a changed control file).

        One advantage of using method |ControlManager.load_file| directly is that it
        supports reading control files that are yet not correctly integrated into a
        complete *HydPy* project by passing its name:

        >>> from hydpy.examples import prepare_full_example_1
        >>> prepare_full_example_1()

        >>> from hydpy.core.filetools import ControlManager
        >>> controlmanager = ControlManager()
        >>> from hydpy import pub, round_, TestIO
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "12h"
        >>> with TestIO():
        ...     controlmanager.projectdir = "LahnH"
        ...     results = controlmanager.load_file(filename="land_dill")


        >>> results["control"]
        area(692.3)
        nmbzones(12)
        sclass(1)
        zonetype(FIELD, FOREST, FIELD, FOREST, FIELD, FOREST, FIELD, FOREST,
                 FIELD, FOREST, FIELD, FOREST)
        zonearea(14.41, 7.06, 70.83, 84.36, 70.97, 198.0, 27.75, 130.0, 27.28,
                 56.94, 1.09, 3.61)
        psi(1.0)
        zonez(2.0, 2.0, 3.0, 3.0, 4.0, 4.0, 5.0, 5.0, 6.0, 6.0, 7.0, 7.0)
        zrelp(3.75)
        zrelt(3.75)
        zrele(3.665)
        pcorr(1.0)
        pcalt(0.1)
        rfcf(1.04283)
        sfcf(1.1)
        tcalt(0.6)
        ecorr(1.0)
        ecalt(0.0)
        epf(0.02)
        etf(0.1)
        ered(0.0)
        ttice(nan)
        icmax(field=1.0, forest=1.5)
        sfdist(1.0)
        smax(inf)
        sred(0.0)
        tt(0.55824)
        ttint(2.0)
        dttm(0.0)
        cfmax(field=4.55853, forest=2.735118)
        cfvar(0.0)
        gmelt(nan)
        gvar(nan)
        cfr(0.05)
        whc(0.1)
        fc(278.0)
        lp(0.9)
        beta(2.54011)
        percmax(1.39636)
        cflux(0.0)
        resparea(True)
        recstep(1200.0)
        alpha(1.0)
        k(0.005618)
        k4(0.05646)
        gamma(0.0)
        maxbaz(0.36728)

        >>> results["percmax"].values
        0.69818

        Passing neither a filename nor an |Element| object raises the following error:

        >>> controlmanager.load_file()
        Traceback (most recent call last):
        ...
        RuntimeError: When trying to load a control file you must either pass its \
name or the responsible Element object.
        """
        if not filename:
            if element:
                filename = element.name
            else:
                raise RuntimeError(
                    "When trying to load a control file you must either pass its name "
                    "or the responsible Element object."
                )
        type(self)._workingpath = self.currentpath
        info = {}
        if element:
            info["element"] = element
        try:
            self.read2dict(filename, info)
        finally:
            type(self)._workingpath = "."
            if clear_registry:
                self._registry.clear()
        return info

    @classmethod
    def read2dict(cls, filename: str, info: Dict[str, Any]) -> None:
        """Read the control parameters from the given path (and its auxiliary paths,
        where appropriate) and store them in the given |dict| object `info`.

        Note that`info` can be used to feed information into the execution of control
        files.  Use this method only if you are entirely sure of how the control
        parameter import of *HydPy* works.  Otherwise, you should most probably prefer
        to use the method |ControlManager.load_file|.
        """
        if not filename.endswith(".py"):
            filename += ".py"
        path = os.path.join(cls._workingpath, filename)
        with hydpy.pub.options.parameterstep(None):
            try:
                if path not in cls._registry:
                    with open(path, encoding=config.ENCODING) as file_:
                        cls._registry[path] = compile(
                            source=file_.read(),
                            filename=filename,
                            mode="exec",
                        )
                exec(cls._registry[path], {}, info)
            except BaseException:
                objecttools.augment_excmessage(
                    f"While trying to load the control file `{path}`"
                )
        if "model" not in info:
            raise RuntimeError(
                f"Model parameters cannot be loaded from control file `{path}`.  "
                f"Please refer to the HydPy documentation on how to prepare control "
                f"files properly."
            )

    @classmethod
    def clear_registry(cls) -> None:
        """Clear the internal registry from control file information."""
        cls._registry.clear()

    def save_file(self, filename: str, text: str) -> None:
        """Save the given text under the given control filename and the current path."""
        if not filename.endswith(".py"):
            filename += ".py"
        path = os.path.join(self.currentpath, filename)
        with open(path, "w", encoding="utf-8") as file_:
            file_.write(text)


class ConditionManager(FileManager):
    """Manager for condition files.

    The base folder name of class |ConditionManager| is:

    >>> from hydpy.core.filetools import ConditionManager
    >>> ConditionManager.BASEDIR
    'conditions'

    Class |ConditionManager| generally works like class |FileManager|.  The following
    examples, based on the `LahnH` example project, explain the additional
    functionalities of the |ConditionManager| specific properties
    |ConditionManager.inputpath| and |ConditionManager.outputpath|:

    >>> from hydpy.examples import prepare_full_example_2
    >>> hp, pub, TestIO = prepare_full_example_2()

    If the current directory named is not defined explicitly, both properties construct
    it following the actual simulation start or end date, respectively:

    >>> from hydpy import repr_
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     repr_(pub.conditionmanager.inputpath)
    ...     repr_(pub.conditionmanager.outputpath)
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_01_00_00_00'
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_05_00_00_00'

    >>> pub.timegrids.sim.firstdate += "1d"
    >>> pub.timegrids.sim.lastdate -= "1d"
    >>> pub.timegrids
    Timegrids(init=Timegrid("1996-01-01 00:00:00",
                            "1996-01-05 00:00:00",
                            "1d"),
              sim=Timegrid("1996-01-02 00:00:00",
                           "1996-01-04 00:00:00",
                           "1d"),
              eval_=Timegrid("1996-01-01 00:00:00",
                             "1996-01-05 00:00:00",
                             "1d"))

    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     repr_(pub.conditionmanager.inputpath)
    ...     repr_(pub.conditionmanager.outputpath)
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_02_00_00_00'
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_04_00_00_00'

    Use the property |FileManager.currentdir| to change the values of both properties:

    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     pub.conditionmanager.currentdir = "test"
    ...     repr_(pub.conditionmanager.inputpath)
    ...     repr_(pub.conditionmanager.outputpath)
    '.../hydpy/tests/iotesting/LahnH/conditions/test'
    '.../hydpy/tests/iotesting/LahnH/conditions/test'

    After deleting the custom value of property |FileManager.currentdir|, both
    properties |ConditionManager.inputpath| and |ConditionManager.outputpath| work as
    before:

    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     del pub.conditionmanager.currentdir
    ...     repr_(pub.conditionmanager.inputpath)
    ...     repr_(pub.conditionmanager.outputpath)
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_02_00_00_00'
    '.../hydpy/tests/iotesting/LahnH/conditions/init_1996_01_04_00_00_00'

    The date-based construction of directory names requires a |Timegrids| object
    available in module |pub|:

    >>> del pub.timegrids
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     repr_(pub.conditionmanager.inputpath)
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: While trying to determine the \
currently relevant input path for loading conditions file, the following error \
occurred: Attribute timegrids of module `pub` is not defined at the moment.

    >>> del pub.timegrids
    >>> with TestIO():    # doctest: +ELLIPSIS
    ...     repr_(pub.conditionmanager.outputpath)
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: While trying to determine the \
currently relevant output path for saving conditions file, the following error \
occurred: Attribute timegrids of module `pub` is not defined at the moment.
    """

    BASEDIR = "conditions"
    DEFAULTDIR = None

    @property
    def inputpath(self) -> str:  # type: ignore[return]
        """The directory path for loading initial conditions.

        See the main documentation on class |ConditionManager| for further information.
        """
        currentdir = self._currentdir
        try:
            if not currentdir:
                to_string = hydpy.pub.timegrids.sim.firstdate.to_string
                self.currentdir = f"init_{to_string('os')}"
            return self.currentpath
        except BaseException:
            objecttools.augment_excmessage(
                "While trying to determine the currently relevant input path for "
                "loading conditions file"
            )
        finally:
            self._currentdir = currentdir

    @property
    def outputpath(self) -> str:  # type: ignore[return]
        """The directory path for saving (final) conditions.

        See the main documentation on class |ConditionManager| for further information.
        """
        currentdir = self._currentdir
        try:
            if not currentdir:
                to_string = hydpy.pub.timegrids.sim.lastdate.to_string
                self.currentdir = f"init_{to_string('os')}"
            return self.currentpath
        except BaseException:
            objecttools.augment_excmessage(
                "While trying to determine the currently relevant output path for "
                "saving conditions file"
            )
        finally:
            self._currentdir = currentdir


class SequenceManager(FileManager):
    """Manager for sequence files.

    Usually, there is only one |SequenceManager| used within each *HydPy* project,
    stored in module |pub|.  This object is responsible for the actual I/O tasks
    related to |IOSequence| objects.

    Working with a complete *HydPy* project, one often does not use the
    |SequenceManager|  directly, except one wishes to load or save time series data in
    a way different from the default settings.  The following examples show the
    essential features of class |SequenceManager| based on the example project
    configuration defined by function |prepare_io_example_1|.

    We prepare the project and select one 0-dimensional sequence of type |Sim| and one
    1-dimensional sequence of type |lland_fluxes.NKor| for the following examples:

    >>> from hydpy.examples import prepare_io_example_1
    >>> nodes, elements = prepare_io_example_1()
    >>> sim = nodes.node2.sequences.sim
    >>> nkor = elements.element2.model.sequences.fluxes.nkor

    We store the time series data of both sequences in ASCII files (methods
    |SequenceManager.save_file| and |IOSequence.save_series| are interchangeable here.
    The last one is only a convenience function for the first one):

    >>> from hydpy import pub
    >>> pub.sequencemanager.filetype = "asc"
    >>> from hydpy import TestIO
    >>> with TestIO():
    ...     pub.sequencemanager.save_file(sim)
    ...     nkor.save_series()

    We can load the file content from the output directory defined by
    |prepare_io_example_1| and print it to check this was successful:

    >>> import os
    >>> from hydpy import round_
    >>> def print_file(filename):
    ...     path = os.path.join("project", "series", "default", filename)
    ...     with TestIO():
    ...         with open(path) as file_:
    ...             lines = file_.readlines()
    ...     print("".join(lines[:3]), end="")
    ...     for line in lines[3:]:
    ...         round_([float(x) for x in line.split()])

    >>> print_file("node2_sim_t.asc")
    Timegrid("2000-01-01 00:00:00+01:00",
             "2000-01-05 00:00:00+01:00",
             "1d")
    64.0
    65.0
    66.0
    67.0
    >>> print_file("element2_flux_nkor.asc")
    Timegrid("2000-01-01 00:00:00+01:00",
             "2000-01-05 00:00:00+01:00",
             "1d")
    16.0, 17.0
    18.0, 19.0
    20.0, 21.0
    22.0, 23.0

    To show that reloading the data works, we set the values of the time series of both
    objects to zero and recover the original values afterwards:

    >>> sim.series = 0.0
    >>> sim.series
    InfoArray([0., 0., 0., 0.])
    >>> nkor.series = 0.0
    >>> nkor.series
    InfoArray([[0., 0.],
               [0., 0.],
               [0., 0.],
               [0., 0.]])
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(sim)
    ...     nkor.load_series()
    >>> sim.series
    InfoArray([64., 65., 66., 67.])
    >>> nkor.series
    InfoArray([[16., 17.],
               [18., 19.],
               [20., 21.],
               [22., 23.]])

    Wrongly formatted ASCII files and incomplete data should result in understandable
    error messages:

    >>> path = os.path.join("project", "series", "default", "node2_sim_t.asc")
    >>> with TestIO():
    ...     with open(path) as file_:
    ...         right = file_.read()
    ...     wrong = right.replace("Timegrid", "timegrid")
    ...     with open(path, "w") as file_:
    ...         _ = file_.write(wrong)
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(sim)
    Traceback (most recent call last):
    ...
    NameError: While trying to load the time-series data of sequence `sim` of node \
`node2`, the following error occurred: name 'timegrid' is not defined

    >>> sim_series = sim.series.copy()
    >>> with TestIO():
    ...     lines = right.split("\\n")
    ...     lines[5] = "nan"
    ...     wrong = "\\n".join(lines)
    ...     with open(path, "w") as file_:
    ...         _ = file_.write(wrong)
    >>> with TestIO():
    ...     pub.sequencemanager.load_file(sim)
    Traceback (most recent call last):
    ...
    RuntimeError: While trying to load the time-series data of sequence `sim` of node \
`node2`, the following error occurred: The series array of sequence `sim` of node \
`node2` contains 1 nan value.
    >>> sim.series = sim_series

    By default, overwriting existing time series files is disabled:

    >>> with TestIO():
    ...     sim.save_series()   # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    OSError: While trying to save the time-series data of sequence `sim` of \
node `node2`, the following error occurred: Sequence `sim` of node `node2` is \
not allowed to overwrite the existing file `...`.
    >>> pub.sequencemanager.overwrite = True
    >>> with TestIO():
    ...     sim.save_series()

    When a sequence comes with a weighting parameter referenced by |property|
    |Variable.refweights|, one can save the averaged time series by using the method
    |IOSequence.save_mean|:

    >>> with TestIO():
    ...     nkor.save_mean()
    >>> print_file("element2_flux_nkor_mean.asc")
    Timegrid("2000-01-01 00:00:00+01:00",
             "2000-01-05 00:00:00+01:00",
             "1d")
    16.5
    18.5
    20.5
    22.5

    Method |IOSequence.save_mean| is strongly related to method
    |IOSequence.average_series|, meaning one can pass the same arguments.  We show this
    by changing the land use classes of `element2` (parameter |lland_control.Lnk|) to
    field (|lland_constants.ACKER|) and water (|lland_constants.WASSER|) and averaging
    the values of sequence |lland_fluxes.NKor| for the single field area only:

    >>> from hydpy.models.lland_v1 import ACKER, WASSER
    >>> nkor.subseqs.seqs.model.parameters.control.lnk = ACKER, WASSER
    >>> with TestIO():
    ...     nkor.save_mean("acker")
    >>> print_file("element2_flux_nkor_mean.asc")
    Timegrid("2000-01-01 00:00:00+01:00",
             "2000-01-05 00:00:00+01:00",
             "1d")
    16.0
    18.0
    20.0
    22.0

    Another option is storing data using |numpy| binary files, which is good for saving
    computation times but possibly problematic for sharing data with colleagues:

    >>> pub.sequencemanager.filetype = "npy"
    >>> with TestIO():
    ...     sim.save_series()
    ...     nkor.save_series()

    The time information (without time zone information) is available within the first
    thirteen entries:

    >>> path = os.path.join("project", "series", "default", "node2_sim_t.npy")
    >>> from hydpy import numpy, print_values
    >>> with TestIO():
    ...     print_values(numpy.load(path))
    2000.0, 1.0, 1.0, 0.0, 0.0, 0.0, 2000.0, 1.0, 5.0, 0.0, 0.0, 0.0,
    86400.0, 64.0, 65.0, 66.0, 67.0

    Reloading the data works as expected:

    >>> sim.series = 0.0
    >>> nkor.series = 0.0
    >>> with TestIO():
    ...     sim.load_series()
    ...     nkor.load_series()
    >>> sim.series
    InfoArray([64., 65., 66., 67.])
    >>> nkor.series
    InfoArray([[16., 17.],
               [18., 19.],
               [20., 21.],
               [22., 23.]])

    Writing mean values into |numpy| binary files is also supported:

    >>> import numpy
    >>> path = os.path.join(
    ...     "project", "series", "default", "element2_flux_nkor_mean.npy")
    >>> with TestIO():
    ...     nkor.save_mean("wasser")
    ...     numpy.load(path)[-4:]
    array([17., 19., 21., 23.])

    Generally, trying to load data for "deactivated" sequences results in the following
    error message:

    >>> nkor.prepare_series(allocate_ram=False)
    >>> with TestIO(clear_all=True):
    ...     pub.sequencemanager.save_file(nkor)
    Traceback (most recent call last):
    ...
    hydpy.core.exceptiontools.AttributeNotReady: Sequence `nkor` of element \
`element2` is not requested to make any time-series data available.

    The third option is to store data in netCDF files, which is explained separately in
    the documentation on class |NetCDFInterface|.
    """

    SUPPORTED_MODES = "npy", "asc", "nc"
    BASEDIR = "series"
    DEFAULTDIR = "default"

    filetype = optiontools.OptionPropertySeriesFileType(
        "asc",
        """Currently active time-series file type.
        
        |SequenceManager.filetype| is an option based on |OptionPropertySeriesFileType|.
        See its documentation for further information.
        """,
    )
    overwrite = optiontools.OptionPropertyBool(
        False,
        """Currently active overwrite flag for time-series files.

        |SequenceManager.overwrite| is an option based on |OptionPropertyBool|.  See 
        its documentation for further information.
        """,
    )
    aggregation = optiontools.OptionPropertySeriesAggregation(
        "none",
        """Currently active aggregation mode for writing time-series files.

        |SequenceManager.aggregation| is an option based on 
        |OptionPropertySeriesAggregation|.  See its documentation for further 
        information.
        """,
    )

    _netcdfreader: Optional[netcdftools.NetCDFInterface] = None
    _netcdfwriter: Optional[netcdftools.NetCDFInterface] = None
    _jitaccesshandler: Optional[netcdftools.JITAccessHandler] = None

    def load_file(self, sequence: sequencetools.IOSequence) -> None:
        """Load data from a data file and pass it to the given |IOSequence|."""
        try:
            if sequence.filetype == "npy":
                sequence.series = sequence.adjust_series(*self._load_npy(sequence))
            elif sequence.filetype == "asc":
                sequence.series = sequence.adjust_series(*self._load_asc(sequence))
            elif sequence.filetype == "nc":
                self._load_nc(sequence)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to load the time-series data of sequence "
                f"{objecttools.devicephrase(sequence)}"
            )

    @staticmethod
    def _load_npy(
        sequence: sequencetools.IOSequence,
    ) -> Tuple[timetools.Timegrid, NDArrayFloat]:
        data = numpy.load(sequence.filepath)
        timegrid_data = timetools.Timegrid.from_array(data)
        return timegrid_data, data[13:]

    @staticmethod
    def _load_asc(
        sequence: sequencetools.IOSequence,
    ) -> Tuple[timetools.Timegrid, NDArrayFloat]:
        filepath = sequence.filepath
        with open(filepath, encoding=config.ENCODING) as file_:
            header = "\n".join([file_.readline() for _ in range(3)])
        timegrid_data = eval(header, {}, {"Timegrid": timetools.Timegrid})
        values = numpy.loadtxt(  # type: ignore[call-overload]
            filepath, skiprows=3, ndmin=min(sequence.NDIM + 1, 2)
        )
        if sequence.NDIM == 2:
            values = values.reshape(*sequence.seriesshape)
        return timegrid_data, values

    def _load_nc(self, sequence: sequencetools.IOSequence) -> None:
        self.netcdfreader.log(sequence, None)

    def save_file(
        self,
        sequence: sequencetools.IOSequence,
        array: Optional[sequencetools.InfoArray] = None,
    ) -> None:
        """Write the data stored in the |IOSequence.series| property of the given
        |IOSequence| into a data file."""
        if array is None:
            array = sequence.aggregate_series()
        try:
            if sequence.filetype == "nc":
                self._save_nc(sequence, array)
            else:
                filepath = sequence.filepath
                if (array is not None) and (array.aggregation != "unmodified"):
                    filepath = f"{filepath[:-4]}_{array.aggregation}{filepath[-4:]}"
                if not sequence.overwrite and os.path.exists(filepath):
                    raise OSError(
                        f"Sequence {objecttools.devicephrase(sequence)} is not allowed "
                        f"to overwrite the existing file `{sequence.filepath}`."
                    )
                if sequence.filetype == "npy":
                    self._save_npy(array, filepath)
                elif sequence.filetype == "asc":
                    self._save_asc(array, filepath)
        except BaseException:
            objecttools.augment_excmessage(
                f"While trying to save the time-series data of sequence "
                f"{objecttools.devicephrase(sequence)}"
            )

    @staticmethod
    def _save_npy(array: NDArrayFloat, filepath: str) -> None:
        numpy.save(filepath, hydpy.pub.timegrids.init.array2series(array))

    @staticmethod
    def _save_asc(array: NDArrayFloat, filepath: str) -> None:
        with open(filepath, "w", encoding=config.ENCODING) as file_:
            file_.write(
                hydpy.pub.timegrids.init.assignrepr(
                    prefix="", style="iso2", utcoffset=hydpy.pub.options.utcoffset
                )
                + "\n"
            )
        if array.ndim == 3:
            array = array.reshape(array.shape[0], -1)
        with open(filepath, "a", encoding=config.ENCODING) as file_:
            numpy.savetxt(file_, array, delimiter="\t")

    def _save_nc(
        self, sequence: sequencetools.IOSequence, array: sequencetools.InfoArray
    ) -> None:
        self.netcdfwriter.log(sequence, array)

    @property
    def netcdfreader(self) -> netcdftools.NetCDFInterface:
        """A |NetCDFInterface| object prepared by method
        |SequenceManager.open_netcdfreader| and to be finalised by method
        |SequenceManager.close_netcdfreader|.

        >>> from hydpy.core.filetools import SequenceManager
        >>> sm = SequenceManager()
        >>> sm.netcdfreader
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle no NetCDF \
reader object.

        >>> sm.open_netcdfreader()
        >>> from hydpy import classname
        >>> classname(sm.netcdfreader)
        'NetCDFInterface'

        >>> sm.close_netcdfreader()
        >>> sm.netcdfreader
        Traceback (most recent call last):
        ...
        RuntimeError: The sequence file manager does currently handle no NetCDF \
reader object.
        """
        if self._netcdfreader is None:
            raise RuntimeError(
                "The sequence file manager does currently handle no NetCDF reader "
                "object."
            )
        return self._netcdfreader

    def open_netcdfreader(self) -> None:
        """Prepare a new |NetCDFInterface| object for reading data."""
        self._netcdfreader = netcdftools.NetCDFInterface()

    def close_netcdfreader(self) -> None:
        """Read data with a prepared |NetCDFInterface| object and delete it
        afterwards."""
        self.netcdfreader.read()
        self._netcdfreader = None

    @contextlib.contextmanager
    def netcdfreading(self) -> Iterator[None]:
        """Prepare a new |NetCDFInterface| object for collecting data at the beginning
        of a with-block and read the data and delete the object at the end of the same
        with-block."""
        self.open_netcdfreader()
        yield
        self.close_netcdfreader()

    @property
    def netcdfwriter(self) -> netcdftools.NetCDFInterface:
        """A |NetCDFInterface| object prepared by method
        |SequenceManager.open_netcdfwriter| and to be finalised by method
        |SequenceManager.close_netcdfwriter|.

        >>> from hydpy.core.filetools import SequenceManager
        >>> sm = SequenceManager()
        >>> sm.netcdfwriter
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager does \
currently handle no NetCDF writer object.

        >>> sm.open_netcdfwriter()
        >>> from hydpy import classname
        >>> classname(sm.netcdfwriter)
        'NetCDFInterface'

        >>> sm.close_netcdfwriter()
        >>> sm.netcdfwriter
        Traceback (most recent call last):
        ...
        hydpy.core.exceptiontools.AttributeNotReady: The sequence file manager does \
currently handle no NetCDF writer object.
        """
        if self._netcdfwriter is None:
            raise exceptiontools.AttributeNotReady(
                "The sequence file manager does currently handle no NetCDF writer "
                "object."
            )
        return self._netcdfwriter

    def open_netcdfwriter(self) -> None:
        """Prepare a new |NetCDFInterface| object for writing data."""
        self._netcdfwriter = netcdftools.NetCDFInterface()

    def close_netcdfwriter(self) -> None:
        """Write data with a prepared |NetCDFInterface| object and delete it
        afterwards."""
        self.netcdfwriter.write()
        self._netcdfwriter = None

    @contextlib.contextmanager
    def netcdfwriting(self) -> Iterator[None]:
        """Prepare a new |NetCDFInterface| object for collecting data at the beginning
        of a with-block and write the data and delete the object at the end of the same
        with-block."""
        self.open_netcdfwriter()
        yield
        self.close_netcdfwriter()

    @contextlib.contextmanager
    def provide_netcdfjitaccess(
        self, deviceorder: Iterable[Union[devicetools.Node, devicetools.Element]]
    ) -> Iterator[None]:
        """Open all required internal NetCDF time-series files.

        This method is only relevant for reading data from or writing data to NetCDF
        files "just in time" during simulation runs.  See the main documentation on
        class |HydPy| for further information.
        """
        try:
            interface = netcdftools.NetCDFInterface()
            with interface.provide_jitaccess(deviceorder) as jitaccesshandler:
                self._jitaccesshandler = jitaccesshandler
                yield
        finally:
            self._jitaccesshandler = None

    def read_netcdfslices(self, idx: int) -> None:
        """Read the time slice relevant for the current simulation step.

        This method is only relevant for reading data from or writing data to NetCDF
        files "just in time" during simulation runs.  See the main documentation on
        class |HydPy| for further information.
        """
        handler = self._jitaccesshandler
        if handler is not None:
            handler.read_slices(idx)

    def write_netcdfslices(self, idx: int) -> None:
        """Write the time slice relevant for the current simulation step.

        This method is only relevant for reading data from or writing data to NetCDF
        files "just in time" during simulation runs.  See the main documentation on
        class |HydPy| for further information.
        """
        handler = self._jitaccesshandler
        if handler is not None:
            handler.write_slices(idx)
