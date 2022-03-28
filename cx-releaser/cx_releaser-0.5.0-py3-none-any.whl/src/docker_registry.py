import base64
import datetime
import re
from collections import defaultdict
from subprocess import PIPE, Popen

import boto3
import docker


class AwsRegistry:
    LATEST_TAG = 'latest'

    def __init__(self, client_aws=None, client_docker=None):
        self.client_aws = client_aws or boto3.client('ecr', region_name='us-east-1')
        self.client_docker = client_docker or docker.from_env()
        self._login()

    def get_all_image_tags(self, image_name, tag_filter=''):
        images = self.client_aws.list_images(repositoryName=image_name)
        results = []
        for image in images['imageIds']:
            if 'imageTag' not in image:
                continue
            tag = image['imageTag']
            if re.search(tag_filter, tag):
                img = self.client_aws.describe_images(
                    repositoryName=image_name,
                    imageIds=[
                        {
                            'imageTag': tag
                        },
                    ]
                )
                pushed_at = img['imageDetails'][0]['imagePushedAt']
                results.append({'tag': tag, 'pushed_at': pushed_at, 'image': image})
        results = sorted(results, key=lambda x: x['pushed_at'], reverse=True)
        return results

    def get_images_on_unique_hash(self, image_name, hash_filter=''):
        images = self.get_all_image_tags(image_name)
        hash_dict = defaultdict(list)
        for image in images:
            digest = image['image']['imageDigest']
            if digest.startswith(hash_filter):
                hash_dict[digest].append(image['tag'])
        return hash_dict

    def pull_image(self, image_name, tag=None):
        if tag is None:
            tag = self.get_all_image_tags(image_name)[0]['tag']
        response = self.client_docker.images.pull(self._get_image_url(image_name, tag), stream=True)
        return response

    def rollback_push(self, image_name, tag, rollback_tag=None, soft=False, as_latest=True):
        if rollback_tag:
            rollback_image = self.get_all_image_tags(image_name, tag_filter=rollback_tag)
            if not rollback_image:
                print(f'Did not find tag {rollback_tag}. Push it first')
                return
            if as_latest:
                response = self.client_aws.batch_get_image(
                    repositoryName=image_name,
                    imageIds=[
                        {
                            'imageTag': rollback_image
                        }
                    ]
                )
                if soft:
                    self.client_aws.put_image(
                        repositoryName=image_name,
                        imageManifest=response['images'][0]['imageManifest'],
                        imageTag=self.LATEST_TAG
                    )
        else:
            self.delete_image(image_name, tag, soft=False)

    def delete_image(self, image_name, tag, soft=True):
        dayint = datetime.date.today()
        images = self.get_all_image_tags(image_name, tag_filter='')
        img_tags = {image['tag']: image['image'] for image in images}
        if not img_tags.get(tag):
            print(f'Did not found images with tag {tag}')
            return
        delete_tag = dayint.strftime("%Y-%m-%d")
        delete_tag = 'DELETEON_' + delete_tag
        response = self.client_aws.batch_get_image(
            repositoryName=image_name,
            imageIds=[
                {
                    'imageTag': tag
                }
            ]
        )
        if soft:
            return self.client_aws.put_image(
                repositoryName=image_name,
                imageManifest=response['images'][0]['imageManifest'],
                imageTag=tag + delete_tag
            )
        else:
            ids = [image['imageId'] for image in response['images']]
            return self.client_aws.batch_delete_image(repositoryName=image_name, imageIds=ids)

    def push_image(self, image_name, tag, local_tag=None, as_latest=False):
        image_tag_name = self._get_image_url(image_name, local_tag or tag, with_registry=False)
        image = self.client_docker.images.get(image_tag_name)
        if as_latest:
            image.tag(self._get_image_url(image_name), self.LATEST_TAG)
        image.tag(self._get_image_url(image_name), tag)
        response = self.client_docker.images.push(self._get_image_url(image_name), tag=tag, stream=False)
        return response

    def get_image_hash(self, image_name, tag):
        image_tag_name = self._get_image_url(image_name, tag, with_registry=False)
        image = self.client_docker.images.get(image_tag_name)
        return image.id

    def get_image_name_and_tag(self, id_):
        image = self.client_docker.images.get(id_)
        return image

    def _login(self):
        token = self.client_aws.get_authorization_token()
        username, password = base64.b64decode(token['authorizationData'][0]['authorizationToken']).decode().split(':')
        registry = token['authorizationData'][0]['proxyEndpoint'].replace("https://", "")
        self.registry_name = registry
        self.auth_config = {'username': username, 'password': password}
        self.client_docker.login(username=username,
                                 password=password,
                                 registry=registry,
                                 reauth=True)
        return self.auth_config
        command = f'docker login --username {username} --password {password} {registry}'
        process = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
        stdout, stderr = process.communicate()
        if not b'Login Succeeded' in stdout:
            raise ValueError(f'Could not login to ecr registry. Got: {stderr}')
        return self.auth_config

    def _get_image_url(self, image, tag=None, with_registry=True):
        suffix, prefix = '', ''
        if tag:
            suffix = f':{tag}'
        if with_registry:
            prefix = f'{self.registry_name}/'
        return f'{prefix}{image}{suffix}'

    def _process_docker_response(self, response, raise_=False):
        if response.get('errorDetails'):
            if raise_:
                raise ValueError(response.get('errorDetails'))
            print(response.get('errorDetails'))
            return
