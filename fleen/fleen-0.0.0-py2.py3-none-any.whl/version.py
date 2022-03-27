"""Version utilities."""
import packaging.version

import fleen

__all__ = ["MAJOR", "MINOR", "MICRO", "RELEASE"]

VERSION = packaging.version.Version(fleen.__version__)
MAJOR = VERSION.major
MINOR = VERSION.minor
MICRO = VERSION.micro
RELEASE = VERSION.release
