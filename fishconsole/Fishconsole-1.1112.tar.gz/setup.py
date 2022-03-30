from setuptools import setup, find_packages


setup(
    name="Fishconsole",
    version="1.1112",
    author="Fish Console",
    author_email="2645602049@qq.com",
    description="小鱼整理的控制台输出辅助模块",

    # 项目主页
    url="https://space.bilibili.com/698117971?spm_id_from=333.1007.0.0",
    # 长描述
    # 你要安装的包，通过 setuptools.find_packages 找到当前目录下有哪些包
    packages=find_packages(),
    # 版本号限制
    python_requires='>=2.7',
    # 依赖包，没有将会自动下载

    install_requires=['requests>=2.0', 'lxml>=4.0', 'easygui'],
)
