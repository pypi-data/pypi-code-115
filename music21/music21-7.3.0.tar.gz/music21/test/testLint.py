# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         testLint.py
# Purpose:      Controller for all lint based testing.
#
# Authors:      Christopher Ariza
#               Michael Scott Cuthbert
#
# Copyright:    Copyright © 2009-2010, 2015 Michael Scott Cuthbert and the music21 Project
# License:      BSD, see license.txt
# ------------------------------------------------------------------------------

# this requires pylint to be installed and available from the command line
import argparse
import os

from music21 import common
from music21.test import commonTest

try:
    # noinspection PyPackageRequirements
    from pylint.lint import Run as pylintRun  # type: ignore
except ImportError:
    pylintRun = None


# see feature list here:
# http://docs.pylint.org/features.html

# W0511:	Used when a warning note as FIXME or XXX is detected.
# W0404:	Reimport %r (imported line %s) Used when a module is re-imported multiple times.

# we do this all the time in unit tests
# R0201:	Method could be a function Used when a method doesn't
#           use its bound instance, and so could be written as a function.
# R0904:	Too many public methods (%s/%s) Used when class has too many public methods,
#            try to reduce this to get a more simple (and so easier to use) class.
# E1101:	%s %r has no %r member Used when a variable is accessed for an non-existent member.
# R0914:	Too many local variables (%s/%s) Used when a function or method has
#           too many local variables.
# many of our test use many local variables
# R0903:	Too few public methods (%s/%s) Used when class has too few public methods,
#                  so be sure it's really worth it.
# R0911:	Too many return statements (%s/%s) Used when a function or method has
#                  too many return statement, making it hard to follow.


def main(fnAccept=None, strict=False):
    '''
    `fnAccept` is a list of one or more files to test.  Otherwise runs all.
    '''
    poolSize = common.cpus()

    if pylintRun is None:
        print("make sure that 'sudo pip3 install pylint' is there. exiting.")
        return

    mg = commonTest.ModuleGather()

    fnPathReject = [
        # 'demos/',
        # 'test/timeGraphs.py',
        '/ext/',
        # 'bar.py',   # used to crash pylint...
        # 'repeat.py',  # used to hang pylint...
        # 'spanner.py',  # used to hang pylint...
    ]

    disable_unless_strict = [
        'too-many-statements',  # someday
        'too-many-arguments',  # definitely! but takes too long to get a fix now...
        'too-many-public-methods',  # maybe, look
        'too-many-branches',  # yes, someday
        'too-many-lines',    # yes, someday.
        'too-many-return-statements',  # we'll see
        'too-many-instance-attributes',  # maybe later
        'inconsistent-return-statements',  # would be nice
        'protected-access',  # this is an important one, but for now we do a lot of
        # x = copy.deepcopy(self); x._volume = ... which is not a problem...
        # also, test suites need to be exempt.
        'keyword-arg-before-vararg',  # a good thing to check for new code, but
        # requires rewriting function signatures in old code

    ]
    disable = [  # These also need to be changed in MUSIC21BASE/.pylintrc
        'arguments-differ',  # -- no -- should be able to add additional arguments so long
        # as initial ones are the same.
        'arguments-renamed',  # not an issue

        'multiple-imports',  # import os, sys -- fine...
        'redefined-variable-type',  # would be good, but currently
        # lines like: if x: y = note.Note() ; else: y = note.Rest()
        # triggers this, even though y doesn't change.
        'no-else-return',  # these are unnecessary but can help show the flow of thinking.
        'cyclic-import',  # we use these inside functions when there's a deep problem.
        'unnecessary-pass',  # nice, but not really a problem...
        'locally-disabled',  # test for this later, but hopefully will know what
        # they're doing
        'consider-using-get',  # if it can figure out that the default value is something
        # simple, we will turn back on, but until then, no.
        'chained-comparison',  # sometimes simpler that way
        # 'duplicate-code',  # needs to ignore strings -- keeps getting doctests...
        'too-many-ancestors',  # -- 8 is okay.
        'fixme',  # known...
        'superfluous-parens',  # nope -- if they make things clearer...
        'no-member',  # important, but too many false positives
        'too-many-locals',   # no
        'bad-whitespace',  # maybe later, but "bad" isn't something I necessarily agree with
        'bad-continuation',  # never remove -- this is a good thing many times.

        # AbstractDiatonicScale.__eq__ shows how this
        # can be fine...
        'too-many-boolean-expressions',

        'unsubscriptable-object',  # unfortunately, thinks that Streams are unsubscriptable.

        # sometimes .keys() is a good test against
        # changing the dictionary size while iterating.
        'consider-iterating-dictionary',
        'consider-using-dict-items',  # readability improvement depends on excellent variable names

        'invalid-name',      # these are good music21 names; fix the regexp instead...
        'no-self-use',       # maybe later
        'too-few-public-methods',  # never remove or set to 1

        'trailing-whitespace',  # should ignore blank lines with tabs

        # just because something is easy to detect doesn't make it bad.
        'trailing-newlines',

        'missing-docstring',    # gets too many well-documented properties
        'star-args',  # no problem with them...
        'unused-argument',
        'import-self',  # fix is either to get rid of it or move away many tests...

        'simplifiable-if-statement',  # NO! NO! NO!
        #  if (x or y and z and q): return True, else: return False,
        #      is a GREAT paradigm -- over "return (x or y and z and q)" and
        #      assuming that it returns a bool...  it's no slower than
        #      the simplification and it's so much clearer.
        'consider-using-enumerate',  # good when i used only once, but
        # x[i] = y[i] is a nice paradigm, even if one can be simplified out.
        'not-callable',  # false positives, for instance on x.next()

        'raise-missing-from',  # later.

    ]
    if not strict:
        disable = disable + disable_unless_strict

    goodNameRx = {'argument-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'attr-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'class-rgx': r'[A-Z_][A-Za-z0-9_]{2,30}$',
                  'function-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'method-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  'module-rgx': r'(([a-z_][a-zA-Z0-9_]*)|([A-Z][a-zA-Z0-9]+))$',
                  'variable-rgx': r'[a-z_][A-Za-z0-9_]{2,30}$',
                  }

    maxArgs = 7 if not strict else 5
    maxBranches = 20 if not strict else 10

    cmd = ['--output-format=parseable',
           r'--dummy-variables-rgx="_$|dummy|unused|i$|j$|junk|counter"',
           '--docstring-min-length=3',
           '--ignore-docstrings=yes',
           '--min-similarity-lines=8',
           '--max-args=' + str(maxArgs),  # should be 5 later, but baby steps
           '--bad-names="foo,shit,fuck,stuff"',  # definitely allow "bar" for barlines
           '--reports=n',
           '--max-branches=' + str(maxBranches),
           '-j ' + str(poolSize),  # multiprocessing!
           r'--ignore-long-lines="converter\.parse"',  # some tiny notation...
           '--max-line-length=100',
           ]
    for gn, gnv in goodNameRx.items():
        cmd.append('--' + gn + '="' + gnv + '"')

    for pyLintId in disable:
        cmd.append(f'--disable={pyLintId}')

    # add entire package
    acceptable = []
    for fp in mg.modulePaths:
        rejectIt = False
        for rejectPath in fnPathReject:
            if rejectPath in fp:
                rejectIt = True
                break
        if rejectIt:
            continue
        if fnAccept:
            rejectIt = True
            for acceptableName in fnAccept:
                if acceptableName in fp:
                    rejectIt = False
                    break
            if rejectIt:
                continue

        acceptable.append(fp)

    cmdFile = cmd + acceptable
    if not acceptable:
        print('No matching files were found.')
        return

    # print(fnAccept)
    # print(' '.join(cmdFile))
    # print(fp)

    try:
        # noinspection PyArgumentList,PyCallingNonCallable
        pylintRun(cmdFile, exit=False)
    except TypeError:
        # noinspection PyCallingNonCallable
        pylintRun(cmdFile, do_exit=False)  # renamed in recent versions


def argRun():
    parser = argparse.ArgumentParser(
        description='Run pylint on music21 according to style guide.')
    parser.add_argument('files', metavar='filename', type=str, nargs='*',
                        help='Files to parse (default nearly all)')
    parser.add_argument('--strict', action='store_true',
                        help='Run the file in strict mode')
    args = parser.parse_args()
    # print(args.files)
    # print(args.strict)
    files = args.files if args.files else None
    if files:
        filesMid = [os.path.abspath(f) for f in files]
        files = []
        for f in filesMid:
            if os.path.exists(f):
                files.append(f)
            else:
                print('skipping ' + f + ': no matching file')
    main(files, args.strict)


if __name__ == '__main__':
    argRun()
    # main(sys.argv[1:])
    # if len(sys.argv) >= 2:
    #     test.main(sys.argv[1:], restoreEnvironmentDefaults=True)
    # else:
    #     test.main(restoreEnvironmentDefaults=True)
    #

