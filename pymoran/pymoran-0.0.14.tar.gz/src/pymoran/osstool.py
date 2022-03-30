import oss2


class AliyunClass:
    def __init__(self, AccessKeyId: str, AccessKeySecret: str, endpoint: str, bucket_name: str):
        '''
        RAM用户的AccessKey信息
        :param AccessKeyId AccessKeyId
        :param AccessKeySecret AccessKeySecret
        :param endpoint Endpoint（地域节点）外网访问地址，带https://
        :param bucket_name Bucket名称
        '''
        self.auth = oss2.Auth(
            AccessKeyId,
            AccessKeySecret
        )
        self.bucket = oss2.Bucket(
            self.auth,
            endpoint,
            bucket_name,
            connect_timeout=30
        )

    def put_object(self, name, file):
        '''
        上传文件
        :param name 文件名称
        :param file 文件
        '''
        self.bucket.put_object(name, file)

    def get_object(self, key, file_name, style):
        '''
        下载文件
        '''
        self.bucket.get_object_to_file(key, file_name, process=style)

    def delete_object(self, key):
        self.bucket.delete_object(key)
