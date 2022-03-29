import boto3

from cx_releaser.config.config import Config
from cx_releaser.src.docker_registry import AwsRegistry
from cx_releaser.src.release import Release


def args(parser):
    push = parser.add_parser('push', help='Push release')
    push.add_argument('--equal_tags', help='Additional tags to add to release image', nargs='+')
    push.add_argument('--auto_incr_version', choices=['minor', 'major', 'patch'], default='minor')
    return parser


def push(tenant, version, conf_path, equal_tags=None, local_version=None, all_tenants=False,
         auto_incr_version='minor'):
    if tenant is None and all_tenants is False:
        raise ValueError('Specify tenant or pass all_tenants')
    conf = Config(conf_path)
    tenants = [conf.get_by(tenant)] if tenant else list(conf.traverse_envs())
    releases = []
    for tenant_conf in tenants:
        registry = AwsRegistry(boto3.client('ecr', region_name='us-east-1',
                                            aws_access_key_id=tenant_conf['aws_access_key_id'],
                                            aws_secret_access_key=tenant_conf['aws_secret_access_key']))
        version = version or tenant_conf.get('version')
        equal_tags = equal_tags or tenant_conf.get('equal_tags')
        release = Release(registry, tenant_conf['image_name'], version, equal_tags=equal_tags,
                          local_name=local_version,
                          incr_version=auto_incr_version)
        if not version:
            release = release.next(remote_sync=True)
        print(f'Preparing release: {release.name} with version: {release.version}')
        releases.append(release)
    for tenant_conf, release in zip(tenants, releases):
        check_is_newest_version, check_is_new_hash = tenant_conf.get('check_is_newest_version'), \
                                                     tenant_conf['check_is_new_hash']
        release.validate_push(check_is_next=check_is_newest_version,
                              check_new_hash=check_is_new_hash)
    for release in releases:
        release.push()
        print(f'Successfully performed release {release.version} on tenant {release.registry_client.registry_name}')
