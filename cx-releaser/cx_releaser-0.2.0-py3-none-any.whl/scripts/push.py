import boto3

from cx_releaser.config.config import Config
from cx_releaser.src.docker_registry import AwsRegistry
from cx_releaser.src.release import Release


def args(parser):
    push = parser.add_parser('push', help='Push release')
    push.add_argument('--equal_tags', help='Additional tags to add to release image', nargs='+')
    push.add_argument('--check_hash', help='Check if pushed image has different hash than already deployed',
                      action='store_true')
    return parser


def push(tenant, version, conf_path, equal_tags=None, local_version=None, all_tenants=False, check_hash=False):
    if tenant is None and all_tenants is False:
        raise ValueError('Specify tenant or pass all_tenants')
    conf = Config(conf_path)
    tenants = [conf.get_by(tenant)] if tenant else conf.traverse_envs()
    for tenant_conf in tenants:
        registry = AwsRegistry(boto3.client('ecr', region_name='us-east-1',
                                            aws_access_key_id=tenant_conf['aws_access_key_id'],
                                            aws_secret_access_key=tenant_conf['aws_secret_access_key']))
        release = Release(registry, tenant_conf['image_name'], version, equal_tags=equal_tags,
                          local_version=local_version)
        if not version:
            release = release.next()
        print(f'Preparing release: {release.name} with version: {release.version}')
        release.push()
        if check_hash:
            tags_diff = set(release.get_equal_tags_from_remote()).difference(set(release.equal_tags))
            if tags_diff:
                release.rollback(all_equal_tags=False)
                raise ValueError(f'Image with same hash has been already deployed for tags {tags_diff}')
        print(f'Successfully performed release {release.version} on tenant {tenant_conf["account_id"]}')
