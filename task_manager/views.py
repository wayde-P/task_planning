from django.shortcuts import render
from django.shortcuts import redirect
from django.http import JsonResponse
from django.http import HttpResponse
from task_manager import mysql_conn
from task_manager import conf
import paramiko
import requests
import json
import time
import re
import hashlib
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

global_url = conf.global_url
global_pkey = conf.pkey_file_path


def get_permission_list(username, request_path):
    # is_login = request.session.get("login", False)
    # if is_login:
    # 查询此用户所有的权限列表和title
    sql = 'select p.link,p.title,p.icon_name from user u,permission p,my_user_to_permission m  ' \
          'where u.user = %s ' \
          'and u.id = m.user_id ' \
          'and p.id = m.permission_id ' \
          'and p.active = 1;'
    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning', 'utf8')
    user_permission_list = mh.find(sql, username)
    mh.close()
    # print(user_permission_list)
    handle_permission_list = []
    for item in user_permission_list:
        if item.get("link") == request_path:
            # print("item.get(\"link\")", item.get("link"))
            item["active"] = True
        handle_permission_list.append(item)
    # print(handle_permission_list)

    return handle_permission_list


def f_ssh(key_file, host, port, command):
    private_key = paramiko.RSAKey.from_private_key_file(key_file)

    # 创建SSH对象
    ssh = paramiko.SSHClient()
    # 允许连接不在know_hosts文件中的主机
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 连接服务器
    ssh.connect(hostname=host, port=port, username='root', pkey=private_key)

    # command = '''
    # cp /var/spool/cron/{user} {user}.`date +%F-%R:%S` && \
    # grep -n '{task_path}' /var/spool/cron/{user} | awk -F\: '{{print $1}}'
    # '''.format(user=db_task_exec_user, task_path=db_task_script_path)
    print(command)
    # 执行命令
    stdin, stdout, stderr = ssh.exec_command(command)
    # print(stdout.readlines()[0].strip())
    # 获取命令结果
    ssh_result = stdout.readlines()

    if len(ssh_result) > 0:
        result = ssh_result[0].strip()
        print("ssh reault:" + result)
    else:
        result = ssh_result

    err_list = stderr.readlines()

    if len(err_list) > 0:
        print("ERROR:" + err_list[0])

    # 关闭连接
    ssh.close()

    return result


def get_user_info(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path


# def get_login__permission(request):
#     def get_login__permission_out(func):
#         def require(*args, **kwargs):
#             if is_login:
#                 if check_permission(username, request_path):
#                     permission_list = get_permission_list(username, request_path)
#                     result = func(*args, **kwargs)
#                     return result
#                 else:
#                     return render(request, "no_permission.html")
#             else:
#                 return redirect("login.html")
#
#         return require
#
#     return get_login__permission_out
#
#
# @get_login__permission(get_user_info)
# def test_upload(request, permission_list):
#     return HttpResponse(permission_list)


def genearteMD5(str):
    # 创建md5对象
    hl = hashlib.md5()

    # Tips
    # 此处必须声明encode
    # 否则报错为：hl.update(str)    Unicode-objects must be encoded before hashing
    hl.update(str.encode(encoding='utf-8'))
    print(hl.hexdigest())
    return hl.hexdigest()


# mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning', 'utf8')

def log(username, request_path, reslute, comment):
    log_sql = "insert into task_plant_log (op_time,username,url_path,result,comment) values (now(),%s,%s,%s,%s)"
    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning', 'utf8')
    if mh.cud(log_sql, (username, request_path, int(reslute), comment)):
        pass
    else:
        print("log error")
    mh.close()


def check_permission(username, request_path):
    # is_login = request.session.get("login", False)
    # if is_login:
    # 查询此用户所有的权限列表
    sql = 'select p.link from user u,permission p,my_user_to_permission m  ' \
          'where u.user = %s ' \
          'and u.id = m.user_id ' \
          'and p.id = m.permission_id'
    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning', 'utf8')
    permission_dict = mh.find(sql, username)
    mh.close()
    # print(permission_list)
    permission_list = []
    for permission in permission_dict:
        permission_list.append(permission.get('link'))
    print("permission_list: ", permission_list)
    if request_path in permission_list:
        return True
    else:
        return False


def login(request):
    if request.method == "GET":
        is_login = request.session.get("login", False)
        if is_login:
            return redirect("task_list.html")
        else:
            return render(request, "signin.html")
            # return HttpResponse(request,"login.html")
    elif request.method == "POST":
        # print(request.POST)
        # print(request.session['login'])
        user_name = request.POST.get("username")
        pass_word = request.POST.get("password")

        # print("requtst.POST", request.POST)
        # sql = "select user,password from user where user=%s"
        # print("select user sql: %s"%(sql))
        # sql_result=mh.find(sql,user_name)
        # user_dict =sql_result[0]
        # print(user_dict)
        login_api = "http://192.168.23.218:8180/innerspore/userCenter/login.do"
        postData = {
            'platform': 1,
            'unionId': user_name,
            'password': pass_word,
        }
        print(request.path)

        # 上传加密过的数据验证
        login_info = requests.post(login_api, data=postData)
        # print(login_info.text)
        # print(type(login_info.text))
        login_info = json.loads(login_info.text)
        # print("登录成功",login_info["success"])

        # 验证登录是否成功
        if login_info["success"]:
            # if pass_word == user_dict[user_name].get("password"):
            request.session['login'] = True
            request.session['username'] = user_name
            request.session.set_expiry(30000)
            # print("session info : ", request.session)
            request_path = request.path
            print(user_name, "login ok")
            log(user_name, request.path, 0, "login success")
            # permission_list = check_permission(username=user_name, request_path=request_path)
            # print("permission list:", permission_list)
            return redirect("task_list.html")
        else:
            log(user_name, request.path, 1, "login fail")
            print(user_name, "login fail")
            # return render(request,"login.html")
            return redirect("login.html")


def index(request):
    return redirect("login.html")


def task_list(request):
    print("this is task list================")
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    print("username: ", username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            # 获取任务列表
            sql = "select * from task_list where 1 = %s"
            mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning',
                                        'utf8')
            task_list_dict = mh.find(sql, 1)
            mh.close()
            # 分页
            paginator = Paginator(task_list_dict, 10, 5)
            page = request.GET.get('page')
            try:
                customer = paginator.page(page)
            except PageNotAnInteger:
                customer = paginator.page(1)
            except EmptyPage:
                customer = paginator.page(paginator.num_pages)

            log(username, request.path, 0, "get task list")
            # print(task_list_dict)
            return render(request, "task_list.html",
                          {"task_list_dict": customer, "permission_list": permission_list,
                           "global_url": global_url})
        else:
            log(username, request.path, 1, "get task list fail , no permission")
            return render(request, "no_permission.html")
    else:
        log(username, request.path, 1, "get task list fail , no login")
        return redirect("login.html")


# 模糊搜索
def task_blurred_search(request):
    print("this is task_blurred_search list================")
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    print("username: ", username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            blurred_char = request.GET.get("blurred")
            if blurred_char is not None:
                # 根据关键字筛选
                find_sql = "select * from task_list where script_path like %s"
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')
                format_blurred = "%" + blurred_char + "%"
                blurred_task_list = mh.find(find_sql, format_blurred)
                # print(select_task_list)
                mh.close()
                # 分页
                paginator = Paginator(blurred_task_list, 10, 5)
                page = request.GET.get('page')
                try:
                    customer = paginator.page(page)
                except PageNotAnInteger:
                    customer = paginator.page(1)
                except EmptyPage:
                    customer = paginator.page(paginator.num_pages)
                return render(request, "task_blurred_list.html",
                              {"task_list_dict": customer, "permission_list": permission_list,
                               "blurred_char": blurred_char, "global_url": global_url})
            else:
                log(username, request.path, 1, "get task list fail , no permission")
                return render(request, "no_permission.html")
        else:
            log(username, request.path, 1, "get task list fail , no login")
            return redirect("login.html")


def task_list_search(request):
    print("this is task list================")
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    print("username: ", username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)

            select_host = request.GET.get("select_host")
            select_user = request.GET.get("select_user")
            # all 函数判断所有参数是否为空同  if and
            if all([select_host, select_user]):
                # 根据主机和用户筛选
                tag = "host_user"
                sql = "select * from task_list where host= %s and exec_user = %s;"
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')
                select_task_list = mh.find(sql, (select_host, select_user))
                # print(select_task_list)
                mh.close()
                # 分页
                paginator = Paginator(select_task_list, 10, 5)
                page = request.GET.get('page')
                try:
                    customer = paginator.page(page)
                except PageNotAnInteger:
                    customer = paginator.page(1)
                except EmptyPage:
                    customer = paginator.page(paginator.num_pages)
                return render(request, "task_search_list.html",
                              {"task_list_dict": customer, "permission_list": permission_list,
                               "host": select_host, "user": select_user, "global_url": global_url})
            else:
                log(username, request.path, 1, "get task list fail , no permission")
                return render(request, "no_permission.html")
        else:
            log(username, request.path, 1, "get task list fail , no login")
            return redirect("login.html")


def report_data(request):
    # print("report_begin: ",report_begin)
    # print("report_end: ",report_end)

    # if report_command_md5 is None or \
    #                 report_result is None or \
    #                 report_lines is None or \
    #                 report_begin is None or \
    #                 command_exc_user is None or \
    #                 report_end is None:
    if request.method == "GET" and len(request.GET) < 13:
        return HttpResponse(content="Missing parameters")
    elif request.method == "GET" and len(request.GET) == 13:
        report_command_md5 = request.GET['report_command_md5']
        report_result = request.GET['report_result']
        report_lines = request.GET['report_lines']
        report_begin_time = request.GET['report_begin']
        report_end_time = request.GET['report_end']
        command_exc_user = request.GET['command_exc_user']
        exc_host = request.GET['exc_host']
        min = request.GET['min']
        hour = request.GET['hour']
        day = request.GET['day']
        month = request.GET['month']
        week = request.GET['week']
        handle_command = request.GET['handle_command']
        if report_begin_time is not None and report_end_time is not None:
            report_begin = time.localtime(int(report_begin_time))
            report_end = time.localtime(int(report_end_time))
        else:
            return HttpResponse(content="time parameters illegal")
        add_history_sql = "insert into task_history(host,report_md5,result,`lines`,start_time,end_time," \
                          "exec_user,`min`,`hour`,`day`,`month`,week,command) " \
                          "values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#', 'task_planning',
                                    'utf8')
        if mh.cud(add_history_sql, (exc_host,
                                    report_command_md5,
                                    int(report_result),
                                    int(report_lines),
                                    report_begin,
                                    report_end,
                                    command_exc_user,
                                    min,
                                    hour,
                                    day,
                                    month,
                                    week,
                                    handle_command)):
            mh.close()
            return HttpResponse(content="ok")
        else:
            mh.close()
            return HttpResponse(content="report error , please check parameters")


def task_history(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            # 判断上传的时间.默认为当前时间至前一天
            if request.method == "POST":
                start_time = request.POST['web_starttime']
                end_time = request.POST['web_endtime']
                # print("post")
            else:
                start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 86400))
                end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
                # print("get")
            print("time is : ", start_time, end_time)

            # 根据id获取历史数据
            task_id = request.GET.get("task_id")
            if task_id:
                task_history_sql = "select h.command,h.start_time,h.end_time,h.exec_user,h.result,h.lines from task_history h,task_list l " \
                                   "where l.id = %s and l.script_path_md5 = h.report_md5 and start_time >= %s and start_time < %s ;"
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')
                task_history_result = mh.find(task_history_sql, (task_id, start_time, end_time))
                mh.close()
                # print("task_history_result: ",task_history_result)
                task_info = task_history_result[0].get("command")
                result_dict = {"starttime": start_time, "endtime": end_time, "hist_result": task_history_result,
                               "task_id": task_id, "permission_list": permission_list, "task_info": task_info,
                               "global_url": global_url}
                #
                info = "task is {}, start time is : {} , endtime is : {}".format(task_info, start_time, end_time)
                log(username, request.path, 0, info)
                return render(request, "task_history.html", result_dict)
            else:
                return redirect("task_list.html")
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def add_task(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            # print("request.methon: ",request.method)
            if request.method == "GET":
                return render(request, "add_task.html", {"permission_list": permission_list})
            elif request.method == "POST":
                task_name = request.POST.get('task_name')
                task_type = request.POST['task_type']
                task_host = request.POST['host']
                exec_user = request.POST['exec_user']
                frequency = request.POST['frequency']
                script_path = request.POST['scirpt_path']
                task_comment = request.POST['comment']
                create_time = time.localtime()
                # 任务加密字符串
                task_str = task_host + re.sub(" +", " ", script_path) + exec_user
                # print(task_str)
                task_md5 = genearteMD5(task_str)

                add_task_sql = "insert into task_list(task_name,host,exec_user,task_type,frequency,script_path_md5,script_path,task_create_time,comment) " \
                               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')
                if mh.cud(add_task_sql, (
                        task_name, task_host, exec_user, task_type, frequency, task_md5, script_path, create_time,
                        task_comment)):
                    mh.close()
                    return render(request, "add_task_return.html")
                    # return HttpResponse(content="<html><body>add task ok,<a herf=\"/task_list.html\">任务列表</a></body></html>")
                else:
                    mh.close()
                    return HttpResponse(content="report error , please check parameters")
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def manage_task_list(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    # print("username: ",username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            if request.method == "GET":
                # try:
                if request.GET.get("del_task_id"):
                    delete_id = request.GET["del_task_id"]
                    # print("=========================================", delete_id)
                    if delete_id:
                        get_task_command_sql = "select script_path from task_list where id = %s ; "
                        mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                    'task_planning', 'utf8')
                        command_info = mh.find(get_task_command_sql, delete_id)[0].get("script_path")
                        print("command_info: ", command_info)
                        mh.close()
                        del_task_sql = "delete from task_list where id = %s"
                        mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                    'task_planning', 'utf8')
                        if mh.cud(del_task_sql, delete_id):
                            mh.close()
                            log(username, request.path, 0, "delete task: {}".format(command_info))
                            return redirect("manage_task_list.html")
                        else:
                            mh.close()
                            return HttpResponse("delete task fail")

                elif request.GET.get("action"):
                    action = int(request.GET.get("action"))
                    task_id = request.GET.get("task_id")
                    host = request.GET.get("host")
                    exec_user = request.GET.get("exec_user")
                    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                'task_planning', 'utf8')
                    get_task_info_sql = "select * from task_list where id = %s"
                    task_info = mh.find(get_task_info_sql, task_id)[0]
                    print("task_infO:   ", task_info)
                    db_task_id = task_info.get("id")
                    db_task_host = task_info.get("host")
                    db_task_exec_user = task_info.get("exec_user")
                    db_task_script_path = task_info.get("script_path")

                    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                'task_planning', 'utf8')
                    command = "grep -n '{task_path}' /var/spool/cron/{user} | awk -F\: '{{print $1}}'" \
                        .format(user=db_task_exec_user, task_path=db_task_script_path)

                    # 获取行数
                    line_num = f_ssh(global_pkey, db_task_host, 3222, command).strip()

                    print("action:", type(action), db_task_id, db_task_host, db_task_exec_user)
                    # action=1 为开启, 0 为关闭
                    if action == 1:
                        print("begin start open task.")
                        # and db_task_id is not None and db_task_host is not None and db_task_exec_user is not None:
                        action_sql = "update task_list set current_status = 1 where id = %s"
                        print(action_sql)
                        if line_num:
                            command = "cd /var/spool/cron/ ; cp {user} {user}.`date +%F-%R:%S` &&" \
                                      " sed -i '{line}s/^#*//' /var/spool/cron/{user} && " \
                                      " grep '{task}' /var/spool/cron/{user} | grep -v '#' | wc -l".format(
                                user=db_task_exec_user, task=db_task_script_path, line=line_num)
                            result = f_ssh(global_pkey, db_task_host, 3222, command)
                            if result == 1:
                                log(username, request.path, 0, "start task: {}".format(db_task_script_path))
                            elif result == 0:
                                log(username, request.path, 0, "start task fail: {}".format(db_task_script_path))
                                return HttpResponse("start fail")
                    # 关闭任务
                    elif action == 0:
                        # and not db_task_id is None and not db_task_host is  None and not db_task_exec_user is None:
                        action_sql = "update task_list set current_status = 0 where id = %s"
                        # print(action_sql)
                        if line_num:
                            print("begin start close task.")
                            command = "cd /var/spool/cron/ ;cp {user} {user}.`date +%F-%R:%S` &&" \
                                      " sed -i '{line}s/^/#/' /var/spool/cron/{user} && " \
                                      " grep '{task}' /var/spool/cron/{user} | grep -v '#' | wc -l".format(
                                user=db_task_exec_user, task=db_task_script_path, line=line_num)
                            result = f_ssh(global_pkey, db_task_host, 3222, command)
                            print("result: ", result, type(result))
                            if int(result) == 0:
                                log(username, request.path, 0, "close task ok: {}".format(db_task_script_path))

                            elif int(result) >= 1:
                                log(username, request.path, 0, "close task fail: {}".format(db_task_script_path))
                                return HttpResponse("stop fail")
                    else:
                        print("action error")

                    if mh.cud(action_sql, task_id):
                        return redirect("manage_task_list.html")
                    else:
                        return HttpResponse("DB oprate error")
                else:
                    sql = "select * from task_list where 1 = %s"
                    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                'task_planning', 'utf8')
                    task_list_dict = mh.find(sql, 1)
                    mh.close()
                    # print("manage task list:",task_list_dict)
                    log(username, request.path, 0, "get task list")
                    return render(request, "manage_task_list.html",
                                  {"task_list_dict": task_list_dict, "permission_list": permission_list,
                                   "global_url": global_url})
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def user_list(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    # print("username: ",username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            if request.method == "GET":
                sql = "select * from user where 1 = %s"
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')
                all_user = mh.find(sql, 1)
                mh.close()
                log(username, request.path, 0, "get user list")
                return_dict = {"all_user": all_user, "permission_list": permission_list, "global_url": global_url}
                return render(request, "user_list.html", return_dict)
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def user_profile(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path
    # print("username: ",username)
    if is_login:
        if check_permission(username, request_path):
            permission_list = get_permission_list(username, request_path)
            if request.method == "GET":
                user_id = request.GET.get("user_id")

                if user_id is None:
                    return redirect("user_list.html")
                # except Exception as e:
                else:
                    get_user_permission_sql = "select U2P.id,U.user,P.title,P.link,P.info " \
                                              "from user U,permission P,my_user_to_permission U2P " \
                                              "where U2P.user_id = U.id and U2P.permission_id = P.id and U.id = %s;"
                    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                'task_planning', 'utf8')
                    user_permission_list = mh.find(get_user_permission_sql, user_id)
                    mh.close()
                    # username=user_permission_list[0].get("user")
                    # print("userperimisiionlist: ",user_permission_list)
                    # print("username: ", username)
                    mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                                'task_planning', 'utf8')
                    get_no_permission_sql = "select id,title,link,info,active,icon_name " \
                                            "from permission where id not in " \
                                            "(select  permission_id from my_user_to_permission where user_id = %s) "
                    no_permission_list = mh.find(get_no_permission_sql, user_id)
                    mh.close()
                    log(username, request.path, 0, "into manager permission page")
                    return_dict = {"no_permission_list": no_permission_list, "username": username, "user_id": user_id,
                                   "user_permission_list": user_permission_list, "permission_list": permission_list,
                                   "global_url": global_url}
                    return render(request, "user_profile.html", return_dict)
            elif request.method == "POST":
                pass
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def permission_manager(request):
    is_login = request.session.get("login", False)
    username = request.session.get("username")
    request_path = request.path

    # print("username: ",username)
    if is_login:
        if check_permission(username, request_path):
            # permission_list = get_permission_list(username, request_path)
            if request.method == "GET":
                user_id = request.GET.get("user_id")
                action = request.GET.get("action")
                permission_id = request.GET.get("permission_id")

                if user_id is None or action is None or permission_id is None:
                    return HttpResponse(content="Missing parameters")
                elif action == "del":
                    permission_sql = "delete from my_user_to_permission where user_id = %s and id = %s"
                    info = "revoke user_id is {}, permission_id is {}".format(user_id, permission_id)
                elif action == "add":
                    permission_sql = "insert into my_user_to_permission (user_id,permission_id) VALUE (%s,%s) ;"
                    info = "add user_id is {}, permission_id is {}".format(user_id, permission_id)
                else:
                    return redirect("user_list.html")
                mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                            'task_planning', 'utf8')

                if mh.cud(permission_sql, (user_id, permission_id)):
                    redirect_url = "/user_profile.html?user_id={}".format(user_id)
                    log(username, request.path, 0, info)
                    # return redirect("/user_profile.html?user_id=%s",user_id)
                    # print(redirect_url)
                    mh.close()
                    return redirect(redirect_url)
                else:
                    mh.close()
                    return HttpResponse(content="db error")

            elif request.method == "POST":
                pass
        else:
            return render(request, "no_permission.html")
    else:
        return redirect("login.html")


def get_user(request):
    is_login = request.session.get("login", False)
    if is_login:
        host = request.GET.get("host")
        all_user_sql = "select exec_user from task_planning.task_list WHERE host = \"%s\" GROUP BY exec_user;" % (host)
        mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                    'task_planning', 'utf8')
        all_user_sql_result = mh.find(all_user_sql)
        mh.close()
        res = []
        print(all_user_sql_result)
        for i in all_user_sql_result:
            res.append([i.get("exec_user")])
        print(res)
        return JsonResponse({"exec_user": res})


def get_host(request):
    is_login = request.session.get("login", False)
    if is_login:
        all_host_sql = "select host from task_planning.task_list GROUP BY host;"
        mh = mysql_conn.MysqlHelper('192.168.23.176', 3306, 'task_planning', 'task_planning!@#',
                                    'task_planning', 'utf8')
        all_host_sql_result = mh.find(all_host_sql)
        mh.close()
        res = []
        print(all_host_sql_result)
        for i in all_host_sql_result:
            res.append([i.get("host")])
        print(res)
        return JsonResponse({"host": res})


def logout(request):
    del request.session['login']
    return redirect('login.html')
