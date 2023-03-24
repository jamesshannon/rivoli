from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Role(_message.Message):
    __slots__ = ["id", "isAdmin", "name", "permissions"]
    class Permission(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    EDIT_CONFIG_FILETYPES: Role.Permission
    EDIT_CONFIG_PARTNER: Role.Permission
    EDIT_CONFIG_RECORDTYPES: Role.Permission
    EDIT_VIEWABLE_FILE_AND_RECORDS: Role.Permission
    ID_FIELD_NUMBER: _ClassVar[int]
    ISADMIN_FIELD_NUMBER: _ClassVar[int]
    LOAD_FILE: Role.Permission
    NAME_FIELD_NUMBER: _ClassVar[int]
    PERMISSIONS_FIELD_NUMBER: _ClassVar[int]
    PERMISSION_UNKNOWN: Role.Permission
    PROCESS_FILE: Role.Permission
    UPLOAD_FILE: Role.Permission
    VIEW_ALL_RECORDS: Role.Permission
    VIEW_CONFIG: Role.Permission
    VIEW_ERROR_RECORDS: Role.Permission
    VIEW_FILE_INFO: Role.Permission
    VIEW_SENSITIVE_FIELDS: Role.Permission
    VIEW_UNREDACTED_FIELDS: Role.Permission
    WORK_ERRORS: Role.Permission
    id: bytes
    isAdmin: bool
    name: str
    permissions: _containers.RepeatedScalarFieldContainer[Role.Permission]
    def __init__(self, id: _Optional[bytes] = ..., name: _Optional[str] = ..., isAdmin: bool = ..., permissions: _Optional[_Iterable[_Union[Role.Permission, str]]] = ...) -> None: ...

class RoleAssignment(_message.Message):
    __slots__ = ["partnerId", "role"]
    PARTNERID_FIELD_NUMBER: _ClassVar[int]
    ROLE_FIELD_NUMBER: _ClassVar[int]
    partnerId: str
    role: Role
    def __init__(self, partnerId: _Optional[str] = ..., role: _Optional[_Union[Role, _Mapping]] = ...) -> None: ...

class User(_message.Message):
    __slots__ = ["active", "id", "roles"]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ROLES_FIELD_NUMBER: _ClassVar[int]
    active: bool
    id: bytes
    roles: _containers.RepeatedCompositeFieldContainer[RoleAssignment]
    def __init__(self, id: _Optional[bytes] = ..., active: bool = ..., roles: _Optional[_Iterable[_Union[RoleAssignment, _Mapping]]] = ...) -> None: ...
