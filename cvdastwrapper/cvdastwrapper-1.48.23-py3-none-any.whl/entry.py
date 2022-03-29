import json
import os
import shutil
import sys

from cvdastwrapper import fuzzallspecs, runall, runconfig

if not os.path.exists(os.path.join(os.getcwd(),"assets")):
    shutil.copytree(os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates/assets"),
                    os.path.join(os.getcwd(), "assets"))


def main():
    if os.path.exists('specslist.json'):
        with open('specslist.json', 'r') as fj:
            spec_data = json.load(fj)

        with open(runconfig.genspeclistpyfname, "w+") as f:
            f.write("#!/usr/bin/python \n")
            f.write("apispeclist=%s" %(spec_data['specs']))

    if sys.argv[1:]:
        if "--generate-tests" in sys.argv[1:]:
            fuzzallspecs.fuzzspecs()
            return
    runall.main()


if __name__ == "__main__":
    main()
