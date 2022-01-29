import json
import os
from base64 import b64decode as bdc
from base64 import b64encode as bec
from datetime import datetime, timedelta

import rsa
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core import serializers
from django.core.files.images import ImageFile
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.views import View
from rest_framework.views import APIView

from .models import UploadImage, User, UserToken

from .errnum import ErrNum
from .token import GetToken, TokenAuthtication

def get_ret(status = ErrNum(0), message = "OK"):
    return {"status": status.value, "Message": message}

def get_ret_data(status = ErrNum(0), message = "OK", data = None):
    return {"status": status.value, "Message": message, "data": data}
# Create your views here.

class ApiView(View):
    def get(self, request, api_name):
        # <view logic>
        try:
            return self.__getattribute__('get_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found " + str(e))

    def post(self, request, api_name):
        print(api_name)
        # <view logic>
        try:
            return self.__getattribute__('post_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found" + str(e))
    
    def _check_session(self, request: HttpRequest, check_login = False):
        #status = request.session.get('is_login', None)
        if check_login:
            token = request.headers.get('Authorization')
            hasToken = None
            if token: hasToken = UserToken.objects.filter(token = token)
            if hasToken: return False, JsonResponse(get_ret(ErrNum.LOGIN, "isLogined")), None
        stats = request.session.get('keys', None)
        isEncode = request.headers.get('encode', 'False')
        if not isEncode.startswith('True'):
            return False, None, None
        if not stats:
            rep = HttpResponse('Encode cannot use', status = 500)
            rep.set_cookie('encode', False)
            return False, rep, None
        return True, None, stats

    def post_auth(self, request: HttpRequest):
        isEncode, rep, stats = self._check_session(request, True)
        if not isEncode and rep is not None: return rep
        data = request.POST.get('data')
        login = None
        print(data)
        login = json.loads(data)
        if isEncode:
            cipher = AES.new(stats, AES.MODE_ECB)
            login = json.loads(cipher.decrypt(bdc(login['encodes'].encode())))
        
        try: user: User = User.objects.get(E_Mail = login['e_mail'])
        except User.DoesNotExist: user = None
        if not user:
            return JsonResponse(get_ret(ErrNum.NO_SUCH, "No Such User " + login['e_mail']))

        check = check_password(login['password'], user.Password)
        if not check:
            return JsonResponse(get_ret(ErrNum.PASSERR, "Password Error"))
        # login code

        request.session['user_id'] = user.id
        request.session['is_login'] = True
        request.session.set_expiry(43200)

        ret_data = serializers.serialize("json", User.objects.filter(id = user.id), fields=('id', 'User_name', 'E_Mail', 'Profile_Pic'))
        token = GetToken(user.Password, user.id)
        UserToken.objects.create(user = user, token = str(token), expiration_time = datetime.now() + timedelta(hours = 12))
        User.objects.filter(id = user.id).update(Last_Login = datetime.now())
        if isEncode: 
            cipher = AES.new(stats, AES.MODE_ECB)
            ret_data = bytes.decode(bec(cipher.encrypt(ret_data)))
            rep = JsonResponse(get_ret_data(ErrNum.OK, "Login ok", ret_data))
            rep.set_cookie('encode', True)
            rep.set_cookie('token', token)
            return rep
        rep = JsonResponse(get_ret_data(ErrNum.OK, "Login ok", ret_data))
        rep['encode'] = False
        rep['token'] = str(token)
        return rep

    def post_get_key(self, request: HttpRequest):
        data = request.POST.get('data')
        userinfo = json.loads(data)
        try:
            pkey = userinfo['pubkey']
        except KeyError:
            return HttpResponse('pubkey not found', status = 500)
        content = request.session.get('keys')
        if not content: content = get_random_bytes(16)
        request.session['keys'] = content
        pubkey = rsa.PublicKey.load_pkcs1(pkey.encode())
        enkey = rsa.encrypt(bec(content), pubkey)
        req = JsonResponse({'encode_key': enkey})
        req['encode'] = True
        return req
    
    def post_add_user(self, request: HttpRequest):
        isEncode, rep, stats = self._check_session(request)
        if not isEncode and rep is not None: return rep
        userinfo = None
        data = request.POST.get('data')
        userinfo = json.loads(data)
        if isEncode:
            cipher = AES.new(stats, AES.MODE_ECB)
            userinfo = json.loads(cipher.decrypt(bdc(userinfo['encodes'].encode())))
        try:
            username = userinfo['username']
            password = userinfo['password']
            e_mail = userinfo['e_mail']
        except KeyError:
            return HttpResponse('attribute not found', status = 500)
        passwd = make_password(password, None, 'pbkdf2_sha256')
        users = User.objects.filter(E_Mail = e_mail)
        if users: return JsonResponse(get_ret(ErrNum.LOGIN, "E_mail is already register"))
        User.objects.create(User_name = username, Password = passwd, E_Mail = e_mail)
        return JsonResponse(get_ret(ErrNum.OK, "Register OK"))
    
    def get_clear(self, request: HttpRequest):
        request.session.flush()
        return JsonResponse(get_ret(ErrNum.OK, "OK"))


class ApiWithTokenView(APIView):
    authentication_classes = [TokenAuthtication, ]

    def get(self, request, api_name):
        # <view logic>
        try:
            return self.__getattribute__('get_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found " + str(e))

    def post(self, request, api_name):
        print(api_name)
        # <view logic>
        try:
            return self.__getattribute__('post_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found " + str(e))

    def get_is_login(self, request: HttpRequest):
        return JsonResponse(get_ret(ErrNum.OK, "Is Login"))

    def get_user_info(self, request: HttpRequest):
        data = serializers.serialize("json", User.objects.filter(id = request.user.id))
        return JsonResponse(get_ret_data(ErrNum.OK, "get OK", data))
    
    def get_get_avatars(self, request: HttpRequest):
        user_id = request.user.id
        media_root = settings.MEDIA_ROOT
        file_list = os.listdir(media_root)
        avatar_list = [{'name':file, 'url':'/media/{}'.format(file)} for file in file_list if os.path.isfile(os.path.join(media_root, file)) \
            and file.startswith(str(user_id)) and file != str(request.user.Profile_Pic)]
        return JsonResponse(get_ret_data(ErrNum.OK, "OK", avatar_list))
    
    def post_logout(self, request: HttpRequest):
        token = request.auth
        l, d = UserToken.objects.filter(token = token).delete()
        print(l, d)
        return JsonResponse(get_ret(ErrNum.OK, "Logout success"))
    
    def post_upload(self, request: HttpRequest):
        user: User = User.objects.get(id = request.user.id)
        user.Profile_Pic = request.FILES.get('file', user.Profile_Pic)
        user.save()
        return JsonResponse(get_ret_data(ErrNum.OK, "get", str(user.Profile_Pic)))
    
    def post_update(self, request: HttpRequest):
        data = request.POST.get('data')
        user_info = json.loads(data)
        User.objects.filter(id = request.user.id).update(User_name = user_info['User_name'], Gender = user_info['Gender'], BirthDay = user_info['BirthDay'],
            QQ = user_info['QQ'], Telephone = user_info['Telephone'], Describe = user_info['Describe'], Secret = user_info['Secret'])
        return JsonResponse(get_ret(ErrNum.OK, "OK"))
    
    def post_change_old_avatar(self, request: HttpRequest):
        user: User = User.objects.get(id = request.user.id)
        new_file = json.loads(request.POST.get('data'))
        user.Profile_Pic = new_file['name']
        user.save()
        return JsonResponse(get_ret_data(ErrNum.OK, "OK", str(user.Profile_Pic)))

    def post_upload_image(self, request: HttpRequest):
        files = request.FILES
        res = []
        for key in files:
            msg_img: UploadImage = UploadImage.objects.create()
            msg_img.image = files[key]
            msg_img.save()
            res.append({'old': key, 'new': str(msg_img.image)})
        return JsonResponse(get_ret_data(ErrNum.OK, "OK", res))


class ApiCommonView(View):
    def get(self, request, api_name):
        # <view logic>
        try:
            return self.__getattribute__('get_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found " + str(e))

    def post(self, request, api_name):
        print(api_name)
        # <view logic>
        try:
            return self.__getattribute__('post_' + api_name)(request)
        except AttributeError as e:
            return HttpResponseNotFound("Api Not Found " + str(e))
