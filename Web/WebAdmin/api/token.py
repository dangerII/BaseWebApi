from django.contrib.auth.hashers import make_password, check_password
from django.http import HttpRequest
from .models import User, UserToken
from base64 import b64encode as bec, b64decode as bdc

from datetime import datetime, timedelta
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

class GetToken():
    def __init__(self, passwd, user_id):
        self.token = make_password(passwd, None, 'pbkdf2_sha256')
        self.token = self.token.replace('pbkdf2_sha256$180000$', '')
        tmp = user_id.bit_length()
        tmp = tmp // 8 + (1 if tmp % 8 != 0 else 0)
        self.token = '_'.join([bytes.decode(bec(user_id.to_bytes(tmp, 'big'))), self.token])
    
    def __str__(self):
        return self.token


class TokenAuthtication(BaseAuthentication):
    def authenticate(self, request: HttpRequest):
        # 1. 在请求头的query_params中获取token
        # token = request.query_params.get('token')

        # 2. 直接在请求头中获取token
        token: str = request.headers.get('Authorization')
        if not token: 
            print('not token')
            raise exceptions.AuthenticationFailed("用户认证失败")
        try: token_obj: UserToken = UserToken.objects.get(token=token)
        except UserToken.DoesNotExist: token_obj = None
        if not token_obj:
            print(token, 'not token_obj')
            raise exceptions.PermissionDenied("用户认证失败")
        
        user_eid, token = token.split('_')[0], token.split('_')[1]

        user_id = int.from_bytes(bdc(user_eid.encode('latin1')), 'big')
        try: user: User = User.objects.get(id = user_id)
        except User.DoesNotExist: user = None

        if not user: 
            print(token_obj, 'not user')
            raise exceptions.PermissionDenied("用户认证失败")
        passwd = user.Password

        if not check_password(passwd, 'pbkdf2_sha256$180000$' + token):
            print(user, 'not passwd')
            raise exceptions.PermissionDenied("用户认证失败")

        datetime_now = datetime.now()
        if token_obj.expiration_time > datetime_now:
            # 在 rest framework 内部会将两个字段赋值给request，以供后续操作使用
            return (token_obj.user, token_obj)
        else:
            raise exceptions.PermissionDenied("用户token过期,请重新登录")

    def authenticate_header(self, request: HttpRequest):
        # 验证失败时，返回的响应头WWW-Authenticate对应的值
        pass
