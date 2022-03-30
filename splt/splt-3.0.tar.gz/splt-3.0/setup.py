# setup.py 是一个 setuptools 的构建脚本，其中包含了项目和代码文件的信息
# 如果没有需要先安装，pip install setuptools
import setuptools

setuptools.setup(
    # 项目的名称
    name="splt",
    # 项目的版本
    version="3.0",
    # 项目的作者
    author="高乐喆",
    # 作者的邮箱
    author_email="gaolezhe@outlook.com",
    # 项目描述
    description="This function will ask you to enter a string, and this program will separate the string word by word",
    # 项目的长描述
    long_description='This function will ask you to enter a string, and this program will separate the string word by word; "S" in parameter sorl refers to screen and "L" refers to list. This position can only be filled with S or L; The usage and meaning of parameters sep, end, file and flush are the same as that of print(); Please import sys module before using this function. Function format: splt (string, sep = "", end = "\n", file = sys.stdout, flush = false, sorl = "L")\Optimization content: 1 Add parameters sorl, Sep, end, file, flush",',
    # 以哪种文本格式显示长描述
    long_description_content_type="text/markdown",  # 所需要的依赖 
    install_requires=[],  # 比如["flask>=0.10"]
    # 项目主页
    url="",
    # 项目中包含的子包，find_packages() 是自动发现根目录中的所有的子包。
    packages=setuptools.find_packages(),
    # 其他信息，这里写了使用 Python3，MIT License许可证，不依赖操作系统。
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
