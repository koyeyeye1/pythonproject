import json
import os
import re

import jenkins
from conf.operationConfig import OperationConfig


class PJenkins(object):
    conf = OperationConfig()

    def __init__(self):
        self.__config = {
            'url': self.conf.get_section_jenkins('url'),
            'username': self.conf.get_section_jenkins('username'),
            'password': self.conf.get_section_jenkins('password'),
            'timeout': int(self.conf.get_section_jenkins('timeout'))
        }
        self.__server = jenkins.Jenkins(**self.__config)

        self.job_name = self.conf.get_section_jenkins('job_name')
        # 关键修改：与 --alluredir=./report/temp 保持一致
        self.allure_results_dir = os.path.join(os.getcwd(), "report", "temp")

    def get_job_number(self):
        """读取jenkins job构建号"""
        build_number = self.__server.get_job_info(self.job_name).get('lastBuild').get('number')
        return build_number

    def get_build_job_status(self):
        """读取构建完成的状态"""
        build_num = self.get_job_number()
        job_status = self.__server.get_build_info(self.job_name, build_num).get('result')
        return job_status

    def get_console_log(self):
        """获取控制台日志"""
        console_log = self.__server.get_build_console_output(self.job_name, self.get_job_number())
        return console_log

    def get_job_description(self):
        """返回job描述信息"""
        description = self.__server.get_job_info(self.job_name).get('description')
        url = self.__server.get_job_info(self.job_name).get('url')

        return description, url

    # def get_build_report(self):
    #     """返回第n次构建的测试报告"""
    #     report = self.__server.get_build_test_report(self.job_name, self.get_job_number())
    #     return report
    #
    # def report_success_or_fail(self):
    #     """统计测试报告用例成功数、失败数、跳过数以及成功率、失败率"""
    #     report_info = self.get_build_report()
    #     pass_count = report_info.get('passCount')
    #     fail_count = report_info.get('failCount')
    #     skip_count = report_info.get('skipCount')
    #     total_count = int(pass_count) + int(fail_count) + int(skip_count)
    #     duration = int(report_info.get('duration'))
    #     hour = duration // 3600
    #     minute = duration % 3600 // 60
    #     seconds = duration % 3600 % 60
    #     execute_duration = f'{hour}时{minute}分{seconds}秒'
    #     content = f'本次测试共执行{total_count}个测试用例，成功：{pass_count}个; 失败：{fail_count}个; 跳过：{skip_count}个; 执行时长：{hour}时{minute}分{seconds}秒'
    #     # 提取测试报告链接
    #     console_log = self.get_console_log()
    #     report_line = re.search(r'http://127.0.0.1:8080/job/pythonproject/allure', console_log).group(0)
    #     report_info = {
    #         'total': total_count,
    #         'pass_count': pass_count,
    #         'fail_count': fail_count,
    #         'skip_count': skip_count,
    #         'execute_duration': execute_duration,
    #         'report_line': report_line
    #     }
    #     return report_info

    def get_allure_report_stats(self):
        """从 Allure 结果文件中统计用例数和时长"""
        pass_count = 0
        fail_count = 0
        skip_count = 0
        total_duration = 0  # 总时长（毫秒）

        # 检查结果目录是否存在
        if not os.path.exists(self.allure_results_dir):
            return {"passCount": 0, "failCount": 0, "skipCount": 0, "duration": 0}

        # 遍历所有 Allure 结果 JSON 文件
        for filename in os.listdir(self.allure_results_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.allure_results_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # 统计状态
                        status = data.get("status")
                        if status == "passed":
                            pass_count += 1
                        elif status == "failed":
                            fail_count += 1
                        elif status == "skipped":
                            skip_count += 1
                        # 累加时长（Allure 结果中 duration 单位为毫秒）
                        total_duration += data.get("duration", 0)
                except Exception as e:
                    print(f"解析 Allure 结果文件 {filename} 失败：{e}")
                    continue

        return {
            "passCount": pass_count,
            "failCount": fail_count,
            "skipCount": skip_count,
            "duration": total_duration  # 毫秒
        }

    def report_success_or_fail(self):
        """统计测试报告数据（适配 Allure）"""
        # 从 Allure 结果文件获取数据（替换原 report_info = self.get_build_report()）
        report_info = self.get_allure_report_stats()

        # 防止 report_info 为 None（增加容错）
        if not report_info:
            report_info = {"passCount": 0, "failCount": 0, "skipCount": 0, "duration": 0}

        # 提取数据（确保默认值为 0，避免类型错误）
        pass_count = report_info.get('passCount', 0)
        fail_count = report_info.get('failCount', 0)
        skip_count = report_info.get('skipCount', 0)
        total_count = pass_count + fail_count + skip_count

        # 处理时长（转换毫秒为时分秒）
        duration_ms = report_info.get('duration', 0)
        duration_seconds = duration_ms // 1000  # 毫秒转秒
        hour = duration_seconds // 3600
        minute = (duration_seconds % 3600) // 60
        seconds = duration_seconds % 60
        execute_duration = f'{hour}时{minute}分{seconds}秒'

        # 生成 Allure 报告地址（直接拼接，无需正则）
        jenkins_url = self.conf.get_section_jenkins('url').rstrip('/')  # 移除可能的斜杠
        build_number = self.get_job_number()
        report_line = f"{jenkins_url}/job/{self.job_name}/{build_number}/allure/"

        # 返回统计结果
        return {
            'total': total_count,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'skip_count': skip_count,
            'execute_duration': execute_duration,
            'report_line': report_line
        }


# if __name__ == '__main__':
#     p = PJenkins()
#     res = p.report_success_or_fail()
    # result = re.search(r'http://192.168.105.36:8088/job/hbjjapi/(.*?)allure', res).group(0)
    # print(res)
    # print(result)
