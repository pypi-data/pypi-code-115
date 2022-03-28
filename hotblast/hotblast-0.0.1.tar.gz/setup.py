import setuptools

with open("hotblast/README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hotblast",
    version="0.0.1",
    author="黄宏哲",
    author_email="2528104776@qq.com",
    description="一个轻型搜索工具。",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/huang-hongzhe/prioritization",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=['hotblast'],
    python_requires=">=3.6",
    entry_points = {
        'console_scripts':[
            'so=hotblast:finding',
            'push=hotblast:push',
            'modifty=hotblast:modifty_conf'
        ]
    }
)