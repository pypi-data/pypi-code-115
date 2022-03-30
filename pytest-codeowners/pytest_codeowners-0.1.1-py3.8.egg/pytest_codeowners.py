from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Set

import pytest
from codeowners import CodeOwners
from pytest import UsageError

__version__ = "0.1.1"


class CodeOwnersConfig(NamedTuple):
    file: Path
    owners: Set[str]


_PATH_OWNERS_CACHE: Dict[str, Set[str]] = {}


def pytest_addoption(parser):
    codeowners_group = parser.getgroup("codeowners", "select test based on codeowners")
    codeowners_group.addoption(
        "--codeowners-file",
        action="store",
        dest="codeowners_file",
        default=None,
        help="CODEOWNERS file location.",
    )
    codeowners_group.addoption(
        "--codeowners-owner",
        action="append",
        dest="codeowners_owners",
        default=None,
        help="Owner defined in CODEOWNERS. Repeat for multiple owners.",
    )


def pytest_report_header(config) -> Optional[List[str]]:
    if (codeowners := _validate_config(config)) is None:
        return

    return [
        "codeowners: selecting tests owned by '{}' from '{}'".format(
            ", ".join(codeowners.owners), codeowners.file
        )
    ]


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest, items: List[pytest.Item]
) -> None:
    if (codeowners := _validate_config(config)) is None:
        return

    path_owners = _load_path_owners(codeowners.file)
    selected_items = []
    for item in items:
        owners = _get_path_owners(path_owners, item.location[0])
        if codeowners.owners.intersection(owners):
            selected_items.append(item)

    # update items in place
    items[:] = selected_items


def _validate_config(config) -> Optional[CodeOwnersConfig]:
    codeowners_file = config.getoption("codeowners_file", None)
    codeowners_owners = config.getoption("codeowners_owners", None)
    if codeowners_file is None and codeowners_owners is None:
        return None

    if codeowners_file is None or codeowners_owners is None:
        raise UsageError(
            "'--codeowners-file' and '--codeowners-owner' must be used together."
        )

    codeowners_path = Path(codeowners_file)
    if not codeowners_path.exists():
        raise UsageError(f"CODEOWNERS file '{codeowners_file}' doesn't exist.")

    return CodeOwnersConfig(codeowners_path, set(codeowners_owners))


def _load_path_owners(codeowners_path: Path) -> CodeOwners:
    return CodeOwners(codeowners_path.read_text("utf-8"))


def _get_path_owners(path_owners, test_file: str) -> Set[str]:
    if test_file not in _PATH_OWNERS_CACHE:
        _PATH_OWNERS_CACHE[test_file] = {
            owner[1] for owner in path_owners.of(test_file)
        }

    return _PATH_OWNERS_CACHE[test_file]
