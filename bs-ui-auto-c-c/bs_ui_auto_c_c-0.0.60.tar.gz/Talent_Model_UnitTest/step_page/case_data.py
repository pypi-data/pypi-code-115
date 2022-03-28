
class case_data:
    """
    用于存储测试用例数据
    """

    def __init__(self):
        pass

    class test_cases_data_dict:
        """
        测试数据
        """
        login_info = {
            'username': 'admin601022@beisen.com',
            'password': 'a1234567'
        }

        add_talent_model_date = {'预期结果': '添加成功'}
        delete_talent_model_date = {'预期结果': '删除成功'}

    class prod_cases_data_dict:
        """
        线上环境
        """

        login_info = {
            'username': 'liyan410071@beisen.com',
            'password': 'Ly199473.!'
        }

        add_talent_model_date = {'预期结果': '添加成功'}
        delete_talent_model_date = {'预期结果': '删除成功'}

    class prod_tools_data:
        """
        线上查询工具所有依赖数据
        """

        def __init__(self):
            pass

    class test_tools_data:
        """
        线上查询工具所有依赖数据
        """

        def __init__(self):
            pass
