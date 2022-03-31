import pytest
from tuxbake.exceptions import TuxbakeRunCmdError
from tuxmake.runtime import Runtime
from pathlib import Path
import os


def test_git_init(oebuild_git_object, tmpdir_factory):

    """
    oebuild_git_object is a gobal fixture defined in conftest file.
    and we are receiving it as a tuple object (oebuild_obj, src_path_1, src_path_2, git_branch_1, git_branch_2, src_dir)
    """
    from tuxbake.utils import git_init

    oebuild_object = oebuild_git_object[0]
    src_dir = oebuild_object.src_dir
    oebuild_object._runtime = Runtime.get(None)
    oebuild_object._runtime.source_dir = Path(src_dir)
    git_init(oebuild_object, src_dir)

    # case when only url is present and not branch
    for git_obj in oebuild_object.git_trees:

        # adding ref also , so as to cover ref if block
        git_obj.ref = f"refs/heads/{git_obj.branch}"
        git_obj.branch = None

    temp_src2 = tmpdir_factory.mktemp("src2")
    oebuild_object._runtime.source_dir = Path(temp_src2)
    git_init(oebuild_object, temp_src2)

    with pytest.raises((TuxbakeRunCmdError, FileNotFoundError)):
        oebuild_object._runtime.source_dir = Path("/some/wrong/folder")
        git_init(oebuild_object, "/some/wrong/folder")


def test_repo_init(oebuild_repo_init_object, tmpdir_factory):
    from tuxbake.utils import repo_init

    oebuild = oebuild_repo_init_object
    oebuild._runtime = Runtime.get(None)
    url, branch, manifest = oebuild.repo.url, oebuild.repo.branch, oebuild.repo.manifest
    temp_src = tmpdir_factory.mktemp("test_repo_init")
    oebuild._runtime.source_dir = Path(temp_src)

    # case - checking with all right parameters ( url, branch, manifest)
    repo_init(oebuild, temp_src)

    # case - checking with all right parameters with a tag.
    oebuild.repo.branch = "refs/tags/1.0.0"
    repo_init(oebuild, temp_src)

    # case - checking with wrong branch name
    oebuild.repo.branch = "some-wrong-branch"
    with pytest.raises(TuxbakeRunCmdError):
        repo_init(oebuild, temp_src)
    oebuild.repo.branch = branch

    # case - checking with wrong url
    oebuild.repo.url = "https://gitlab.com/some/wrong/url"
    with pytest.raises(TuxbakeRunCmdError):
        repo_init(oebuild, temp_src)
    oebuild.repo.url = url

    # case - checking with local manifest file
    manifest_path = oebuild.local_manifest
    local_manifest = os.path.abspath(manifest_path)
    repo_init(oebuild, temp_src, local_manifest)

    # case - checking with wrong manishfest file name
    oebuild.repo.manifest = "some-wrong-name.xml"
    with pytest.raises(TuxbakeRunCmdError):
        repo_init(oebuild, temp_src)
