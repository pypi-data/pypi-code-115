import boto3

from cx_releaser.config.config import Config
from cx_releaser.src.docker_registry import AwsRegistry
from cx_releaser.src.release import Release


def args(parser):
    rollback = parser.add_parser('rollback', help='Rollback release')
    rollback.add_argument('--prev_release', help='Version of prev release')
    return parser


def rollback(tenant, version, conf_path, prev_release_version=None, local_version=None, all_tenants=False):
    if tenant is None and all_tenants is False:
        raise ValueError('Specify tenant or pass all_tenants')
    conf = Config(conf_path)
    tenants = [conf.get_by(tenant)] if tenant else conf.traverse_envs()
    for tenant_conf in tenants:
        registry = AwsRegistry(boto3.client('ecr', region_name='us-east-1',
                                            aws_access_key_id=tenant_conf['aws_access_key_id'],
                                            aws_secret_access_key=tenant_conf['aws_secret_access_key']))
        if not version:
            release = Release.from_remote(tenant_conf['image_name'], registry, local_version)
        else:
            release = Release(registry, tenant_conf['image_name'], version)
        prev_release = None
        if prev_release_version:
            prev_release = Release(registry, tenant_conf['image_name'], prev_release_version, local_version=local_version)
        release.rollback(prev_release)
        print(f'Successfully performed rollback of version {release.version} on all tenants')
