# -*- coding: utf-8 -*-
import shutil
import pytest
import os
import webbrowser
from conf.setting import REPORT_TYPE

if __name__ == '__main__':

    # if REPORT_TYPE == 'allure':
    #     pytest.main(
    #         ['-s', '-v', '--alluredir=./report/temp', './testcase', '--clean-alluredir',
    #          '--junitxml=./report/results.xml'])
    #
    #     shutil.copy('./environment.xml', './report/temp')
    #     os.system(f'allure serve ./report/temp')

    # 如果要用jenkins就用下面这段代码 否则服务器会卡住而不进行卡一步
    if REPORT_TYPE == 'allure':
        pytest.main([
            '-s', '-v',
            '--alluredir=./report/temp',  # 生成 Allure 原始结果
            './testcase',
            '--clean-alluredir',
            '--junitxml=./report/results.xml'
        ])

        # 复制环境配置文件（保持不变）
        shutil.copy('./environment.xml', './report/temp')

        # 关键修改：用 allure generate 生成静态报告，替代 allure serve
        # 生成到 ./report/allure-report 目录（与 Jenkins 配置的 Report path 对应）
        os.system(f'allure generate ./report/temp -o ./report/allure-report --clean')

    elif REPORT_TYPE == 'tm':
        pytest.main(['-vs', '--pytest-tmreport-name=testReport.html', '--pytest-tmreport-path=./report/tmreport'])
        webbrowser.open_new_tab(os.getcwd() + '/report/tmreport/testReport.html')
