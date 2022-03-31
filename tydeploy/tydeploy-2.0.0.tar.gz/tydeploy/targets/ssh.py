import os
import sys
import paramiko
from queue import Queue
from io import StringIO
from paramiko import SSHClient, SFTPClient, Agent, RSAKey, SSHException
from typing import Any, Dict, Tuple
from ..thread_pool import ThreadPool
from ..functions import unixpath, virtual_root


def sftp_unixpath(*values: str) -> str:
    return "/" + unixpath(*values)


def sftp_exists(sftp: SFTPClient, path: str):
    try:
        sftp.stat(path)
        return True
    except FileNotFoundError:
        return False


def sftp_mkdir(sftp: SFTPClient, path: str):
    if not sftp_exists(sftp, path):
        print(f"SSH：> mkdir '{path}'")
        sftp.mkdir(path)


def clear_dest_if_need(target: Dict[str, Any], ssh: SSHClient, dest: str, force: bool):
    if not target.get("clear", False):
        return
    if (not force) and (input(f"SSH: 是否清空目录 '{dest}'？ (y/n) ").lower() != "y"):
        print("错误：SSH：部署中止。", file=sys.stderr)
        sys.exit(-0x2A000001)
    command = f"rm -rf '{dest}'"
    print(f"SSH：> {command}")
    ssh.exec_command(command)


def connect_ssh(target: Dict[str, Any]) -> Tuple[SSHClient, SFTPClient]:
    private_keys = list()
    if target["credential"].get("agent", False):
        agent = Agent()
        print("SSH：使用 ssh 代理中的私钥")
        for keys in agent.get_keys():
            private_keys.append(keys)
            print("SSH：在代理中发现了一个私钥")
    if target["credential"].get("private_key") is not None:
        print("SSH：使用配置文件中的私钥")
        private_keys.append(RSAKey.from_private_key(StringIO(target["credential"]["private_key"].strip())))
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"SSH：共有 {len(private_keys)} 个私钥备选")
    for i in range(len(private_keys)):
        print(f"SSH：正在尝试私钥 {i + 1}")
        try:
            ssh.connect(hostname=target["host"], port=target["port"], username=target["user"], pkey=private_keys[i])
            sftp = ssh.open_sftp()
            return ssh, sftp
        except SSHException:
            print(f"SSH：私钥 {i + 1} 不适用于所选的服务器")
            continue
    print("SSH：认证失败，所有备选私钥都无法用于登录所配置的服务器")
    sys.exit(-0x2A000002)


def ensure_dirs_created(sftp: SFTPClient, src: str, dest: str):
    for src_basedir, dirname_list, _ in os.walk(src):
        dest_basedir = sftp_unixpath(dest, virtual_root(src_basedir, src))
        for dirname in dirname_list:
            sftp_mkdir(sftp, sftp_unixpath(dest_basedir, dirname))


def deploy(target: Dict[str, Any], force: bool):
    print("SSH：开始部署")
    print(f"SSH：部署自 {target['source']}")
    print(f"SSH：正在连接 {target['user']}@{target['host']}:{target['port']}")
    ssh, sftp = connect_ssh(target)
    source_abspath = os.path.abspath(target["source"])
    dest_abspath = sftp.normalize(target['dest'])
    print(f"SSH：{source_abspath} -> {dest_abspath}")
    clear_dest_if_need(target, ssh, dest_abspath, force)

    run_scripts(ssh, target, "pre")
    print("SSH：正在建立索引并创建目录")
    sftp_mkdir(sftp, dest_abspath)
    ensure_dirs_created(sftp, source_abspath, dest_abspath)
    pool = generate_tasks(source_abspath, dest_abspath)
    run_upload_tasks_thread_pool(ssh, pool, target)

    run_scripts(ssh, target, "post")
    sftp.close()
    ssh.close()
    print("SSH：部署完成")


def run_scripts(ssh: SSHClient, target: Dict[str, Any], name: str):
    commands = target.get("script", {}).get(name)
    if commands is None:
        print(f"SSH：{name}-deploy 没有可以运行的脚本")
        return
    print(f"SSH：开始执行 {name}-deploy 脚本")
    for command in commands:
        print(f"SSH：> {command}")
        stdin, stdout, stderr = ssh.exec_command(command)
        for line in stdout.readlines():
            print(f"SSH：< stdout: {line.strip()}")
        for line in stderr.readlines():
            print(f"SSH：< stderr: {line.strip()}")


def generate_tasks(src: str, dest: str) -> ThreadPool:
    thread_pool = ThreadPool()
    for src_basedir, _, files in os.walk(src):
        dest_basedir = sftp_unixpath(dest, virtual_root(src_basedir, src))
        for file in files:
            thread_pool.add_task({"src": os.path.join(src_basedir, file), "dest": "/" + unixpath(dest_basedir, file)})
    return thread_pool


def run_upload_tasks_thread_pool(ssh: SSHClient, pool: ThreadPool, target: Dict[str, Any]):
    def upload_file(queue: Queue):
        task_sftp = ssh.open_sftp()
        while True:
            task = queue.get()
            task_sftp.put(task["src"], task["dest"])
            queue.task_done()

    pool.start(worker=upload_file)
    pool.wait_complete("SSH：正在上传 {finished}/{total} {bar} {pct} ({time})", end_text="SSH：上传完成")
