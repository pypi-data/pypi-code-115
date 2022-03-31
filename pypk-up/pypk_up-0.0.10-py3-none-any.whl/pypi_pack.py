import os


""" exe打包程序 """
def pypi_pack():
    type_choose = input('1、生成spec配置文件\n2、通过spec打包exe文件\n0、退出程序\n请根据序号选择操作：')
    if type_choose == '1':
        base_path = input('请填入当前项目根目录：') + '/'
        data_path = input('请填入图标等静态资源所在目录：') + '/'
        console = input('是否显示控制窗口？(y:开启,n:不开启)：')
        if console.lower() == 'y':
            the_console = True
        else:
            the_console = False


if __name__ == '__main__':
    pypi_pack()