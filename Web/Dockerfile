FROM python:3.7
ENV PYTHONUNBUFFERED 1

# 添加 Debian 清华镜像源
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bak

RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list

RUN apt-get update
RUN apt-get install python3-dev default-libmysqlclient-dev cron -y

RUN mkdir /code
WORKDIR /code
# 添加 pip 清华镜像源
RUN pip install pip -U -i https://pypi.tuna.tsinghua.edu.cn/simple
ADD requirements.txt /code/
# 添加 pip 清华镜像源
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN rm -r /code