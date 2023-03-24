from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Function(_message.Message):
    __slots__ = ["active", "deprecated", "description", "id", "jsCode", "jsFunction", "name", "parameters", "partnerId", "pythonFunction", "sqlCode", "system", "type"]
    class DataType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class FunctionType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class ApiEndpoint(_message.Message):
        __slots__ = []
        def __init__(self) -> None: ...
    class Parameter(_message.Message):
        __slots__ = ["defaultValue", "description", "type", "variableName"]
        DEFAULTVALUE_FIELD_NUMBER: _ClassVar[int]
        DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
        TYPE_FIELD_NUMBER: _ClassVar[int]
        VARIABLENAME_FIELD_NUMBER: _ClassVar[int]
        defaultValue: str
        description: str
        type: Function.DataType
        variableName: str
        def __init__(self, variableName: _Optional[str] = ..., type: _Optional[_Union[Function.DataType, str]] = ..., description: _Optional[str] = ..., defaultValue: _Optional[str] = ...) -> None: ...
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    BOOLEAN: Function.DataType
    DATA_TYPE_UNKNOWN: Function.DataType
    DEPRECATED_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    FIELD_RENDERER: Function.FunctionType
    FIELD_VALIDATION: Function.FunctionType
    FLOAT: Function.DataType
    FUNCTION_TYPE_UNKNOWN: Function.FunctionType
    GLOBAL_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INTEGER: Function.DataType
    JSCODE_FIELD_NUMBER: _ClassVar[int]
    JSFUNCTION_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    PARTNERID_FIELD_NUMBER: _ClassVar[int]
    PYTHONFUNCTION_FIELD_NUMBER: _ClassVar[int]
    RECORD_DUPLICATION_CHECK: Function.FunctionType
    RECORD_ROLLBACK: Function.FunctionType
    RECORD_UPLOAD: Function.FunctionType
    RECORD_VALIDATION: Function.FunctionType
    SQLCODE_FIELD_NUMBER: _ClassVar[int]
    STRING: Function.DataType
    SYSTEM_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    active: bool
    deprecated: bool
    description: str
    id: str
    jsCode: str
    jsFunction: str
    name: str
    parameters: _containers.RepeatedCompositeFieldContainer[Function.Parameter]
    partnerId: _containers.RepeatedScalarFieldContainer[str]
    pythonFunction: str
    sqlCode: str
    system: bool
    type: Function.FunctionType
    def __init__(self, id: _Optional[str] = ..., active: bool = ..., deprecated: bool = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., type: _Optional[_Union[Function.FunctionType, str]] = ..., system: bool = ..., partnerId: _Optional[_Iterable[str]] = ..., pythonFunction: _Optional[str] = ..., jsFunction: _Optional[str] = ..., jsCode: _Optional[str] = ..., sqlCode: _Optional[str] = ..., parameters: _Optional[_Iterable[_Union[Function.Parameter, _Mapping]]] = ..., **kwargs) -> None: ...

class FunctionResource(_message.Message):
    __slots__ = ["active", "credentials", "hostname", "id", "name", "partnerId", "qpmLimit"]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    CREDENTIALS_FIELD_NUMBER: _ClassVar[int]
    HOSTNAME_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARTNERID_FIELD_NUMBER: _ClassVar[int]
    QPMLIMIT_FIELD_NUMBER: _ClassVar[int]
    active: bool
    credentials: str
    hostname: str
    id: str
    name: str
    partnerId: str
    qpmLimit: int
    def __init__(self, id: _Optional[str] = ..., partnerId: _Optional[str] = ..., active: bool = ..., name: _Optional[str] = ..., credentials: _Optional[str] = ..., hostname: _Optional[str] = ..., qpmLimit: _Optional[int] = ...) -> None: ...
