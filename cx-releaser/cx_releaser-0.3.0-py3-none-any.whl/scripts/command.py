from argparse import ArgumentParser

from cx_releaser.scripts.push import args as push_args, push
from cx_releaser.scripts.rollback import args as rollback_args, rollback


def main():
    parser = ArgumentParser()
    parser.add_argument('--tenant', help='Name of tenant (AWS account id) to perform operation')
    parser.add_argument('--all_tenants', action='store_true', help='If passed perform operation on all tenants')
    parser.add_argument('--version', help='Version of release')
    parser.add_argument('--local_version', help='Tag of local image to make release for')
    parser.add_argument('--config_path', help='Path to config file')
    subparsers = parser.add_subparsers(dest='command')
    rollback_args(subparsers), push_args(subparsers)
    args = parser.parse_args()
    if args.command == 'push':
        push(args.tenant, args.version, args.config_path,
             args.equal_tags, all_tenants=args.all_tenants, local_version=args.local_version,
             check_hash=args.check_hash)
    elif args.command == 'rollback':
        rollback(args.tenant, args.version, args.config_path,
                 args.prev_release, all_tenants=args.all_tenants, local_version=args.local_version)
    else:
        raise ValueError('Unknown command. Available push and rollback')


if __name__ == "__main__":
    main()

