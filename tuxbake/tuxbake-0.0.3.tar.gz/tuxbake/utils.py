import os
import shutil
from tuxbake.exceptions import TuxbakeRunCmdError


def run_cmd(cmd, runtime):
    fmt_cmd = ["bash", "-c", cmd]
    ret_code = runtime.run_cmd(fmt_cmd, offline=False)
    if not ret_code:
        raise TuxbakeRunCmdError(f"Failed to run '{cmd}'")


def repo_init(oebuild, src_dir, local_manifest=None, pinned_manifest=None):
    cmd = f"repo init -u {oebuild.repo.url} -b {oebuild.repo.branch} -m {oebuild.repo.manifest}"
    run_cmd(cmd, oebuild._runtime)
    if pinned_manifest:
        oebuild._runtime.log(
            f"Copying {pinned_manifest} .repo/manifests/{oebuild.repo.manifest}"
        )
        shutil.copy(
            pinned_manifest, f"{src_dir}/.repo/manifests/{oebuild.repo.manifest}"
        )

    if local_manifest:
        oebuild._runtime.log("Adding local_manifest")
        os.makedirs(f"{src_dir}/.repo/local_manifests/", exist_ok=True)
        shutil.copy(local_manifest, f"{src_dir}/.repo/local_manifests/")

    cmd = "repo sync -j16"
    run_cmd(cmd, oebuild._runtime)
    cmd = "repo manifest -r -o pinned-manifest.xml"
    run_cmd(cmd, oebuild._runtime)


def git_init(oebuild, src_dir):
    for git_object in oebuild.git_trees:
        url = git_object.url
        branch = git_object.branch
        ref = git_object.ref
        sha = git_object.sha
        basename = os.path.splitext(os.path.basename(url))[0]
        if branch:
            cmd = f"git clone {url} -b {branch}"
        else:
            cmd = f"git clone {url}"
        run_cmd(cmd, oebuild._runtime)
        if ref:
            cmd = f"cd {src_dir}/{basename} && git fetch origin {ref}:{ref}-local"
            run_cmd(cmd, oebuild._runtime)
            cmd = f"cd {src_dir}/{basename} && git checkout {ref}-local"
            run_cmd(cmd, oebuild._runtime)
        if sha:
            cmd = f"cd {src_dir}/{basename} && git checkout {sha}"
            run_cmd(cmd, oebuild._runtime)
