from semantic_version import Version

from cx_releaser.src.docker_registry import AwsRegistry


class Release:
    version_pattern = '[0-9]\.[0-9]\.[0-9]'

    def __init__(self, registry_client: AwsRegistry, name, version, local_version=None, equal_tags=None,
                 incr_version='minor'):
        """
        :param registry_client:  registry client like AwsRegistry client
        :param name: name of image
        :param version: version (tag) of the image
        :param local_version: version (tag) of the image present on localhost
        :param equal_tags: additional tags for the image (beside version)
        :param incr_version: minor, major or patch. Which version we should increment/decrement
        """
        self.registry_client = registry_client
        self.name = name
        self.equal_tags = equal_tags or []
        self.version = version
        self.local_version = local_version or version
        self.incr_version = incr_version
        self.hash = self.registry_client.get_image_hash(self.name, self.local_version)

    def get_equal_tags_from_remote(self, hash_filter=''):
        equal_tags = []
        hashes = self.registry_client.get_images_on_unique_hash(self.name, hash_filter=hash_filter)
        for hash, tags in hashes.items():
            if self.version in tags:
                equal_tags.extend(tags)
        if equal_tags:
            equal_tags.remove(self.version)
        return equal_tags

    def push(self):
        images = self.registry_client.get_all_image_tags(self.name, tag_filter=self.version_pattern)
        self._check_is_next_release(images)
        self.registry_client.push_image(self.name, self.version, local_tag=self.local_version)
        for tag in self.equal_tags:
            self.registry_client.push_image(self.name, str(tag), local_tag=self.local_version)

    def rollback(self, prev_release=None, all_equal_tags=True):
        equal_tags = self.get_equal_tags_from_remote() if all_equal_tags else self.equal_tags
        self.registry_client.delete_image(self.name, str(self.version), soft=False)
        for tag in equal_tags:
            self.registry_client.delete_image(self.name, str(tag), soft=False)
        if prev_release:
            prev_release.push()

    def _check_is_next_release(self, images):
        versions = []
        for image in images:
            versions.append(Version(image['tag']))
        versions.sort(reverse=True)
        if versions and versions[0] > Version.coerce(self.version):
            raise ValueError(f'Deployed version {str(versions[0])} is greater than current {str(self.version)}')

    def get_versions(self, last=True):
        images = self.registry_client.get_all_image_tags(self.name, tag_filter=self.version_pattern)
        versions = []
        for image in images:
            versions.append(Version(image['tag']))
        versions.sort(reverse=True)
        if last:
            return versions[0] if versions else Version.coerce('0.0.0')
        return versions

    def next(self):
        return type(self)(self.registry_client, self.name, str(getattr(self.get_versions(last=True),
                                                                       f'next_{self.incr_version}')()),
                          self.local_version, self.equal_tags, self.incr_version)

    @classmethod
    def from_remote(cls, name, client: AwsRegistry, local_tag=None):
        images = client.get_all_image_tags(name, tag_filter=cls.version_pattern)
        if not images:
            raise ValueError(f'Could not fetch from remote. No versions found for pattern {cls.version_pattern}')
        newest = images[0]['tag']
        return cls(client, name, newest, local_version=local_tag)

    @classmethod
    def get_all_from_remote(cls, name, client: AwsRegistry, local_tag=None):
        images = client.get_all_image_tags(name, tag_filter=cls.version_pattern)
        results = []
        for image in images:
            results.append(cls(client, name, image['tag'], local_version=local_tag))
        return results
