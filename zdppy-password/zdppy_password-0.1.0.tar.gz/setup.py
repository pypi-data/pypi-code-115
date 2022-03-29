# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['zdppy_password', 'zdppy_password.libs', 'zdppy_password.libs.rsa']

package_data = \
{'': ['*']}

install_requires = \
['pycryptodome>=3.14.1,<4.0.0',
 'rsa>=4.8,<5.0',
 'tinyec>=0.4.0,<0.5.0',
 'zdppy-log>=0.1.7,<0.2.0']

setup_kwargs = {
    'name': 'zdppy-password',
    'version': '0.1.0',
    'description': 'Python用于处理数据和文件加密解密的库',
    'long_description': '# zdppy_password\nPython密码工具\n\n项目地址：https://github.com/zhangdapeng520/zdppy_password\n\n## 版本历史\n- 2022年3月29日 版本0.1.0 兼容Python和Go的AES RSA加密解密算法\n\n## 常用命令\n生成私钥\n```shell\nopenssl genrsa -out private.pem 1024\n```\n\n生成公钥\n```shell\nopenssl rsa -in private.pem -pubout -out public.pem\n```\n\n## 使用案例\n### 案例1：AES加密和解密\n```python\nfrom zdppy_password.aes import Aes\n\naes = Aes()\nres = aes.encrypt(b\'{"cmd": 3000, "msg": "ok"}\').decode(encoding=\'utf-8\')\nprint(res)\nprint(aes.decrypt(res))\n\n# 从go复制过来的\nprint(aes.decrypt("0qg69fOjmE0oR59muWdXoWhr5d4Z0XyQaC69684mAsw="))\n```\n\n## 案例2：RSA加密和解密\n```python\nfrom zdppy_password.rsa import Rsa\nimport json\n\nrsa = Rsa()\n\ndata = {"username": "张大鹏", "age": 22}\ndata = json.dumps(data)\nprint(data)\n\n# 加密\nsecret = rsa.encrypt(data, "public.pem")\n\n# 解密\nprint(json.loads(rsa.decrypt(secret, "private.pem")))\n\n# 从go复制过来的\ndata = "NoA3e0HDMhj7nrwKUx975lUZgjRIA1ZFcEBLeAvgYQ7Nu7toic7xXtg9qmD+wr6soZzb6Gl37H1I5j9OlOTR9igQ+p1pXPOWo47DyDpw3UjiQ6eOAYmyT53lMUGylLZIKHhnbpea5Qpjl+dHrWVYsQ864/asS1ewe9k2hR+BlkBuZSP8p6oiJ+BBOVYckqPFf6PWBjAFGAMridMXglYrKZ2v7+QdwU4mq2YEBVD5XdY70lIEg4XIY8Wb6n5tBB5XkzLsqd22XcBhnEPGLmMC4fuEMyLptH5dMGF/Ogi9YDAP/rKvzdTTpFXPLPh5eeqMMXAS5+AigE1jx1M3w+7IUw=="\nprint(rsa.decrypt(data, "private.pem"))\n```',
    'author': 'zhangdapeng520',
    'author_email': 'pygosuperman@outlook.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://github.com/zhangdapeng520/zdppy_password',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
