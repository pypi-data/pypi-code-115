import logging

from felia._internal import RootCommand

logger = logging.getLogger('SSH')
h = logging.StreamHandler()
h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - | %(message)s"))
logger.addHandler(h)
logger.setLevel(logging.INFO)


class SSH(RootCommand):
    __name__ = 'ssh'
    globals = globals()

    def set_params(self):
        self.add_param("-T",
                       help_text="测试连通性, ssh -T git@github.com")

    def t_github(self):
        getattr(self, 'T')()("git@github.com")


class SSHKeygen(RootCommand):
    """

    install: apt-get install ssh
    重启ssh服务: /etc/init.d/ssh restart
    """
    __name__ = 'ssh-keygen'
    globals = globals()
    use_shell = True

    def set_params(self):
        """

        :return:
        """
        self.add_param("-t",
                       help_text="[dsa | ecdsa | ecdsa-sk | ed25519 | ed25519-sk | rsa]")


ssh = SSH()
ssh_keygen = SSHKeygen()
