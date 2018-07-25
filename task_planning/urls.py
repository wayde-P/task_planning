"""task_planning URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from task_manager import views

urlpatterns = [
    url(r'^admin/', admin.site.urls,name='admin'),
    # url('base', views.base),
    url('login.html', views.login,name='login.html'),
    url('logout.html', views.logout,name='logout.html'),
    url('^task_list.html$', views.task_list, name='task_list.html'),
    url('^manage_task_list.html$', views.manage_task_list,name='manage_task_list.html'),
    url('task_history.html', views.task_history,name='task_history.html'),
    url('report_data', views.report_data,name='report_data'),
    url('index.html', views.index,name='index.html'),
    url('add_task.html', views.add_task,name='add_task.html'),
    url('user_list.html', views.user_list,name='user_list.html'),
    url('test_upload.html', views.test_upload,name='test_upload.html'),
    url('user_profile.html', views.user_profile,name='user_profile.html'),
    url('permission_manager.html', views.permission_manager,name='permission_manager.html'),
]
