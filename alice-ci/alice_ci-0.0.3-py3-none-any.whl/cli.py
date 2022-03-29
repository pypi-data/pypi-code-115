import os
import argparse

from alice.utils import ConfigParser
from alice.runnerfactory import Factory
from alice.exceptions import ConfigException, NonZeroRetcode, RunnerError


def gen_env(self, param_list):
    env_vars = {}
    for item in param_list:
        item_parts = item.split("=")
        if len(item_parts) == 2:
            env_vars[item_parts[0]] = item_parts[1]
        else:
            raise ConfigException(f"Invalid parameter: {item}")
    return env_vars


def parse_jobs(args):
    try:
        factory = Factory()
        if len(args.env) > 0:
            factory.update_runners({"env": gen_env(args.env)})
        jobParser = ConfigParser(args.input, factory)

        print("Begin pipeline steps...")
        for step in args.steps:
            if step in jobParser.jobs:
                jobParser.execute_job(step)
                print(f"[Step] {step}: SUCCESS")
            else:
                print(f"Step {step} not found in {args.input}")
                exit(1)
    except ConfigException as e:
        print(f"Configuration error-> {e}")
        exit(1)
    except NonZeroRetcode:
        print("FAILED")
        exit(1)
    except RunnerError as e:
        print(f"RunnerError-> {e}")


def main():
    parser = argparse.ArgumentParser(prog="alice")
    parser.add_argument("steps", nargs='+')
    parser.add_argument("-i", "--input", default="alice-ci.yaml")
    parser.add_argument("-e", "--env", nargs='*', default=[])
    parser.add_argument("-a", "--addrunner", nargs='*', default=[])
    args = parser.parse_args()
    if not os.path.isfile(args.input):
        print(f"No such file: {args.input}")
        exit(1)
    parse_jobs(args)


if __name__ == "__main__":
    main()
