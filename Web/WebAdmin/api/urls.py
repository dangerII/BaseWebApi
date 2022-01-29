from django.urls import re_path

from .views import ApiCommonView, ApiView, ApiWithTokenView

urlpatterns = [
    re_path(r'^auth/(\w+)/$', ApiView.as_view()),
    re_path(r'^api/(\w+)/$', ApiWithTokenView.as_view()),
    re_path(r'^message/(\w+)/$', ApiCommonView.as_view()),
]