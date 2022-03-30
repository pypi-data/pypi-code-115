# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['secretfs']

package_data = \
{'': ['*'], 'secretfs': ['etc/*']}

install_requires = \
['fusepy>=3.0.0,<4.0.0', 'psutil>=5.9.0,<6.0.0']

entry_points = \
{'console_scripts': ['secretfs = secretfs:main']}

setup_kwargs = {
    'name': 'secretfs',
    'version': '0.1.0',
    'description': 'SecretFS is a security focused FUSE filesystem providing fine-grained access control to application secrets in a hardened Linux, MacOS, and FreeBSD.',
    'long_description': '\nSecretFS is a security focused FUSE filesystem providing fine-grained access control to application secrets in a hardened Linux, MacOS, and FreeBSD. It mirrors an existing directory tree into a read-only FUSE volume and grants or denies applications\' access to files based on the user-defined ACLs (access control lists). The logic of protecting the secrets is handled by the filesystem itself with no code changes to the application.\n\nSecretFS ACLs can restrict access to a specific process, running with a specific command line, as a specific user and/or group, and optionally within a defined time limit. It enables security practices highlighted in [this blog post](http://https://blog.forcesunseen.com/stop-storing-secrets-in-environment-variables "this blog post"), which recommends storing your app secrets on ephemeral mounts allowing access only at the apps\' initialization, so in case the app is compromised later during its runtime the attacker won\'t be able to fetch the secrets.\n\nAdditionally SecretFS can prohibit listing the directory and hide the contents of the shadow volume using the --disable-ls option.\n\n\nInstallation\n------------\n\n1. `sudo pip install secretfs` (or install without sudo and symlink `secretfs` script into the root\'s $PATH)\n2. find the installed `etc/secretfs.conf-example` file, edit to create your ACLs and save as `/etc/secretfs.conf`\n\n### Prerequisites\n\n- Python3\n- FUSE\n\n    Ubuntu: `sudo apt-get install fuse`\n\n    OSX Homebrew: `brew install macfuse`\n\n\n### Creating ACLs\n\nACLs are defined in `/etc/secretfs.conf` as follows:\n\n```\n# [rule_id] - any id or name of the ACL rule; must be unique\n#   path    - path to the the secret, relative to the root directory specified at mount time\n#   process - full path to the process requesting access\n#   cmdline - full command line following the process executable;\n#              empty string or no value means empty command line\n#   user    - uid or name of the user to grant access to;\n#              \'*\' means any user is allowed\n#   group   - gid or name of the group to grant access to\n#              \'*\' means any group is allowed\n#   ttl     - time since the process creation during which access will be granted, in seconds;\n#              0 or no value means don\'t enforce the time limit\n\n[app-foo-secret1-rule1]\npath = secret1.txt\nprocess = /usr/bin/foo\ncmdline = secret1.txt\nuser = ubuntu\ngroup = *\n;ttl = 0        -- no time limit\n\n[app-foo-secret2.pem]\npath = subdir/secret2.txt\n...\n\n```\n\nAll attempts to access files on the secretfs volume are logged into `/var/log/secretfs.log` (or to stdout if running with `--foreground`).\nAfter mounting the SecretFS volume try accessing the secrets from your application; then find the corresponding entry in the log and create the ACL entry using the captured information. Restart SecretFS and try accessing it again to verify the new ACL rule results in a match, and access is granted as intended.\n\n\nMounting\n--------\n\nAs with any FUSE-based filesystem, there are several ways to mount SecretFS\n\n1. From the command line:\n\n        $ sudo secretfs <mountpoint> <directory containing secrets>\n    e.g.\n\n        $ sudo secretfs /mnt/secrets /opt/secrets-store/\n\n   or more expicitly, using Python:\n\n        $ sudo python3 /path/to/secretfs.py /mnt/secrets /opt/secrets-store/\n\n2. With `mount.fuse` command:\n\n        $ sudo mount.fuse secretfs#/mnt/secrets /opt/secrets-store/\n\n   or more expicitly:\n\n        $ sudo mount.fuse /path/to/secretfs.py#/mnt/secrets /opt/secrets-store/\n\n   Debugging:\n\n        sudo python3 secretfs.py --verbose --foreground /mnt/secrets /opt/secrets-store/\n\n3. `/etc/fstab` entry\n\n        secretfs#/mnt/secrets /opt/secrets-store/ fuse auto 0 0\n\n   or more expicitly:\n\n        /path/to/secretfs.py#/mnt/secrets /opt/secrets-store/ fuse auto 0 0\n\n   Specifying command line options in fstab:\n\n        secretfs#/mnt/secrets /opt/secrets-store/ fuse --disable-ls,--verbose 0 0\n\n   then run `sudo mount -a` to mount, `umount /mnt/secrets` to unmount\n\n\nGotchas\n-------\n\nNote that catching the process path for the ACL can be non-intuitive. One may be starting their application with `/usr/bin/python`, but it unwinds into something like `"/usr/local/Cellar/python@2/2.7.17_1/Frameworks/Python.framework/Versions/2.7/Resources/Python.app/Contents/MacOS/Python"` in the secretfs access log. That\'s why reviewing the log is the recommended way to creating ACLs.\n\nSame strictness applies to the command line (`cmdline` in the ACL rule). SecretFS will distinguish between `cat secret.txt` and `cat ./secret.txt`.\n\nWhen running in the terminal, `secretfs.py` would normally terminate on Ctrl-C (or Command+C), and unmount its volume, unless the resource is busy (e.g. there\'s an active bash shell with `cd /mnt/secrets`). In this case FUSE will silently ignore the termination request. Just cd out of the mount point directory and it should unmount fine.\n\n\nDISCLAIMER\n----------\n\nSecretFS is an experimental project and has not been evaluated by independent security experts. Use at your own risk.\nroot has full access to all secrets and can\'t be restricted by SecretFS. Has not been tested on FreeBSD.\n\n\nDEMO\n----\n(See demo/ascii-demo.gif or view it on GitHub)\n\n![SecretFS gif demo](demo/ascii-demo.gif)\n',
    'author': 'Oscar Ibatullin',
    'author_email': 'oscar.ibatullin@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/obormot/secretfs',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
