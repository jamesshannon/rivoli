FROM python:3.10

WORKDIR /usr/rivoli

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_ROOT_USER_ACTION ignore

RUN pip install --upgrade pip

COPY requirements.txt ./
COPY requirements_build.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_build.txt

COPY src ./src

COPY build/protos ./protos
RUN python -m grpc_tools.protoc --proto_path=./protos \
    --pyi_out=./src/ --python_out=./src/ protos/rivoli/protos/*

COPY build/third_party ./third_party

COPY generate_function_entities.py ./
COPY upsert_functions.py ./

ENV PYTHONPATH /usr/rivoli/third_party:/usr/rivoli/src

ENTRYPOINT [ "celery", "-A", "rivoli.celery_app" ]
# Worker by default. Beat also supported
CMD [ "worker" ]
