## Django-based web api framework
Run the api service using docker-compose.
```shell
docker-compose -p webapi -d
```

### Add get/post api in `Web/WebAdmin/api/view.py`
1. Add api before auth
```python
class ApiView:
    def post_xxx_yyy(self): ...
    def get_xxx_yyy(self): ...
```
To access api use http protocal to get/post the url /auth/xxx_yyy

2. Add api after auth with token
```python
class ApiWithTokenView:
    def post_xxx_yyy(self): ...
    def get_xxx_yyy(self): ...
```
To access api use http protocal to get/post the url /api/xxx_yyy

3. Add common api
```python
class ApiCommonView:
    def post_xxx_yyy(self): ...
    def get_xxx_yyy(self): ...
```
To access api use http protocal to get/post the url /message/xxx_yyy
