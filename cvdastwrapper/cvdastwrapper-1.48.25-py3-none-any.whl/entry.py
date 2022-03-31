import os
import shutil
import sys

from cvdastwrapper import fuzzallspecs, runall

if not os.path.exists(os.path.join(os.getcwd(),"assets")):
    shutil.copytree(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/assets"),
                    os.path.join(os.getcwd(), "assets"))


def main():
    if sys.argv[1:]:
        if "--generate-tests" in sys.argv[1:]:
            fuzzallspecs.fuzzspecs()
            return
    runall.main()


if __name__ == "__main__":
    main()
