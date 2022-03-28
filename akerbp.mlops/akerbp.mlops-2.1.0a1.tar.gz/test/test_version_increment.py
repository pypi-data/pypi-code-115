import os
from increment_package_version import increment_version, get_current_version

def reset_version(path_to_version_file):
    with open(path_to_version_file, "r+") as f: 
        f.truncate(0)
        f.write("0.0.0")

def tag_version_as_pre_prelease(path_to_version_file):
    with open(path_to_version_file, "r+") as f: 
        f.truncate(0)
        f.write("1.0.0-alpha")


def test_increment_version_major_increment_in_test(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    expected_new_version = f"{int(major)+1}.{minor}.{patch}-alpha"
    commit_msg = "This is a major update with breaking changes, in test environment"
    new_version = increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    reset_version(path_to_version_file)
    assert new_version == expected_new_version

def test_increment_version_minor_increment_in_test(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    expected_new_version = f"{major}.{int(minor)+1}.{patch}-alpha"
    commit_msg = "This is a minor update without breaking changes, in test environment"
    new_version = increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    reset_version(path_to_version_file)
    assert new_version == expected_new_version

def test_increment_version_patch_increment_in_test(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    expected_new_version = f"{major}.{minor}.{int(patch)+1}-alpha"
    commit_msg = "This is a bugfix"
    new_version = increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    reset_version(path_to_version_file)
    assert new_version == expected_new_version

def test_increment_version_major_increment_in_prod(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    commit_msg = "This is a major update with breaking changes, in prod environment"
    increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    os.environ["ENV"] = "prod"
    new_version_in_prod = increment_version(path_to_version_file, test=True, commit_msg="")
    expected_new_version = f"{int(major)+1}.{minor}.{patch}"
    reset_version(path_to_version_file)
    os.environ["ENV"] = "test"
    assert new_version_in_prod == expected_new_version

def test_increment_version_minor_increment_in_prod(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    commit_msg = "This is a minor update without breaking changes, in prod environment"
    increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    os.environ["ENV"] = "prod"
    new_version_in_prod = increment_version(path_to_version_file, test=True, commit_msg="")
    expected_new_version = f"{major}.{int(minor)+1}.{patch}"
    reset_version(path_to_version_file)
    os.environ["ENV"] = "test"
    assert new_version_in_prod == expected_new_version

def test_increment_version_patch_increment_in_prod(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    version, _, _ = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    commit_msg = "This is just a patch in prod"
    increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    os.environ["ENV"] = "prod"
    new_version_in_prod = increment_version(path_to_version_file, test=True, commit_msg="")
    expected_new_version = f"{major}.{minor}.{int(patch)+1}"
    reset_version(path_to_version_file)
    os.environ["ENV"] = "test"
    assert new_version_in_prod == expected_new_version

def test_increment_version_increment_pre_release_version(path_to_version_file=os.path.abspath("./test/test_version.txt")):
    os.environ["ENV"] = "test"
    tag_version_as_pre_prelease(path_to_version_file)
    version, _, pre_release_number = get_current_version(path_to_version_file)
    major, minor, patch = version.split(".")
    expected_version = f"{major}.{minor}.{patch}-alpha{int(pre_release_number)+1}"    
    commit_msg = "This is a pre-release: only increment alpha number"
    new_version = increment_version(path_to_version_file, test=True, commit_msg=commit_msg)
    reset_version(path_to_version_file)
    assert new_version == expected_version
    


    