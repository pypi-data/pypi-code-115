# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2020 Andrew Rechnitzer
# Copyright (C) 2020-2022 Colin B. Macdonald

from plom.plom_exceptions import (
    PlomConflict,
    PlomRangeException,
)
from plom.create import with_manager_messenger
from plom.rules import censorStudentName, censorStudentNumber
from .buildClasslist import get_demo_classlist


@with_manager_messenger
def upload_classlist(classlist, *, msgr):
    """Uploads a classlist file to the server.

    Arguments:
        classdict (list): list of dict, each has at least keys `"id"` and
            `"studentName"`, optionally other fields too.
        msgr (plom.Messenger/tuple): either a connected Messenger or a
            tuple appropriate for credientials.
    """
    _ultra_raw_upload_classlist(classlist, msgr)


def _raw_upload_classlist(classlist, msgr):
    # TODO: does this distinct only exist for the mock test?  Maybe not worth it!
    try:
        _ultra_raw_upload_classlist(classlist, msgr)
    finally:
        msgr.closeUser()
        msgr.stop()


def _ultra_raw_upload_classlist(classlist, msgr):
    # TODO: clean up this chain viz the mock test
    try:
        msgr.upload_classlist(classlist)
        print(f"Uploaded classlist of length {len(classlist)}.")
        print(
            "  First student:  {} - {}".format(
                censorStudentNumber(classlist[0]["id"]),
                censorStudentName(classlist[0]["studentName"]),
            )
        )
        print(
            "  Last student:  {} - {}".format(
                censorStudentNumber(classlist[-1]["id"]),
                censorStudentName(classlist[-1]["studentName"]),
            )
        )
    except PlomRangeException as e:
        print(
            "Error: classlist lead to the following specification error:\n"
            "  {}\n"
            "Perhaps classlist is too large for specTest.numberToProduce?".format(e)
        )
        raise
    except PlomConflict:
        print("Error: Server already has a classlist, see help (TODO: add force?).")
        raise


@with_manager_messenger
def upload_demo_classlist(*, msgr):
    """Uploads the demo classlist file to the server.

    Keyword Args:
        msgr (plom.Messenger/tuple): either a connected Messenger or a
            tuple appropriate for credientials.
    """
    print("Using demo classlist - DO NOT DO THIS FOR A REAL TEST")
    classlist = get_demo_classlist()
    _ultra_raw_upload_classlist(classlist, msgr)
