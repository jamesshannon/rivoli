from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Destination(_message.Message):
    __slots__ = ["active", "automatic", "name", "type"]
    class DestinationType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    AUTOMATIC_FIELD_NUMBER: _ClassVar[int]
    DESTINATION_UNKNOWN: Destination.DestinationType
    DOWNLOAD: Destination.DestinationType
    FILE: Destination.DestinationType
    NAME_FIELD_NUMBER: _ClassVar[int]
    PROGRAMMATIC: Destination.DestinationType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    active: bool
    automatic: bool
    name: str
    type: Destination.DestinationType
    def __init__(self, name: _Optional[str] = ..., type: _Optional[_Union[Destination.DestinationType, str]] = ..., active: bool = ..., automatic: bool = ...) -> None: ...

class FieldType(_message.Message):
    __slots__ = ["active", "charRange", "columnIndex", "description", "headerColumn", "id", "isSensitive", "isSharedKey", "name", "renderer", "validations"]
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    CHARRANGE_FIELD_NUMBER: _ClassVar[int]
    COLUMNINDEX_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    HEADERCOLUMN_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    ISSENSITIVE_FIELD_NUMBER: _ClassVar[int]
    ISSHAREDKEY_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RENDERER_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONS_FIELD_NUMBER: _ClassVar[int]
    active: bool
    charRange: str
    columnIndex: int
    description: str
    headerColumn: str
    id: str
    isSensitive: bool
    isSharedKey: bool
    name: str
    renderer: FunctionConfig
    validations: _containers.RepeatedCompositeFieldContainer[FunctionConfig]
    def __init__(self, id: _Optional[str] = ..., active: bool = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., isSharedKey: bool = ..., isSensitive: bool = ..., renderer: _Optional[_Union[FunctionConfig, _Mapping]] = ..., charRange: _Optional[str] = ..., headerColumn: _Optional[str] = ..., columnIndex: _Optional[int] = ..., validations: _Optional[_Iterable[_Union[FunctionConfig, _Mapping]]] = ...) -> None: ...

class FileType(_message.Message):
    __slots__ = ["active", "delimitedSeparator", "destinations", "fileMatches", "filenameDateFormat", "filenameDateRegexp", "filenameTagRegexps", "format", "hasHeader", "id", "name", "recordTypes", "referencedFiles", "requireReview", "staticTags"]
    class Format(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class RequireReview(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class DelimitedFileFormat(_message.Message):
        __slots__ = ["delimiter", "hasHeader"]
        DELIMITER_FIELD_NUMBER: _ClassVar[int]
        HASHEADER_FIELD_NUMBER: _ClassVar[int]
        delimiter: str
        hasHeader: str
        def __init__(self, hasHeader: _Optional[str] = ..., delimiter: _Optional[str] = ...) -> None: ...
    class ReferencedFiles(_message.Message):
        __slots__ = ["fileTypeId", "requireMatchedDate"]
        FILETYPEID_FIELD_NUMBER: _ClassVar[int]
        REQUIREMATCHEDDATE_FIELD_NUMBER: _ClassVar[int]
        fileTypeId: str
        requireMatchedDate: bool
        def __init__(self, fileTypeId: _Optional[str] = ..., requireMatchedDate: bool = ...) -> None: ...
    class StaticTagsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    DELIMITEDSEPARATOR_FIELD_NUMBER: _ClassVar[int]
    DESTINATIONS_FIELD_NUMBER: _ClassVar[int]
    FILEMATCHES_FIELD_NUMBER: _ClassVar[int]
    FILENAMEDATEFORMAT_FIELD_NUMBER: _ClassVar[int]
    FILENAMEDATEREGEXP_FIELD_NUMBER: _ClassVar[int]
    FILENAMETAGREGEXPS_FIELD_NUMBER: _ClassVar[int]
    FLAT_FILE_DELIMITED: FileType.Format
    FLAT_FILE_FIXED_WIDTH: FileType.Format
    FORMAT_FIELD_NUMBER: _ClassVar[int]
    FORMAT_UNKNOWN: FileType.Format
    HASHEADER_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    INGESTION_ALWAYS: FileType.RequireReview
    INGESTION_ON_ERRORS: FileType.RequireReview
    NAME_FIELD_NUMBER: _ClassVar[int]
    RECORDTYPES_FIELD_NUMBER: _ClassVar[int]
    REFERENCEDFILES_FIELD_NUMBER: _ClassVar[int]
    REQUIREREVIEW_FIELD_NUMBER: _ClassVar[int]
    REQUIRE_UNKNOWN: FileType.RequireReview
    STATICTAGS_FIELD_NUMBER: _ClassVar[int]
    active: bool
    delimitedSeparator: str
    destinations: _containers.RepeatedCompositeFieldContainer[Destination]
    fileMatches: _containers.RepeatedScalarFieldContainer[str]
    filenameDateFormat: str
    filenameDateRegexp: str
    filenameTagRegexps: _containers.RepeatedScalarFieldContainer[str]
    format: FileType.Format
    hasHeader: bool
    id: str
    name: str
    recordTypes: _containers.RepeatedCompositeFieldContainer[RecordType]
    referencedFiles: _containers.RepeatedCompositeFieldContainer[FileType.ReferencedFiles]
    requireReview: FileType.RequireReview
    staticTags: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., active: bool = ..., name: _Optional[str] = ..., format: _Optional[_Union[FileType.Format, str]] = ..., fileMatches: _Optional[_Iterable[str]] = ..., filenameDateFormat: _Optional[str] = ..., filenameDateRegexp: _Optional[str] = ..., filenameTagRegexps: _Optional[_Iterable[str]] = ..., staticTags: _Optional[_Mapping[str, str]] = ..., hasHeader: bool = ..., delimitedSeparator: _Optional[str] = ..., referencedFiles: _Optional[_Iterable[_Union[FileType.ReferencedFiles, _Mapping]]] = ..., requireReview: _Optional[_Union[FileType.RequireReview, str]] = ..., recordTypes: _Optional[_Iterable[_Union[RecordType, _Mapping]]] = ..., destinations: _Optional[_Iterable[_Union[Destination, _Mapping]]] = ...) -> None: ...

class FunctionConfig(_message.Message):
    __slots__ = ["functionId", "id", "parameters"]
    FUNCTIONID_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    functionId: str
    id: str
    parameters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, id: _Optional[str] = ..., functionId: _Optional[str] = ..., parameters: _Optional[_Iterable[str]] = ...) -> None: ...

class Partner(_message.Message):
    __slots__ = ["active", "fileTypes", "id", "name", "staticTags"]
    class StaticTagsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    ACTIVE_FIELD_NUMBER: _ClassVar[int]
    FILETYPES_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    STATICTAGS_FIELD_NUMBER: _ClassVar[int]
    active: bool
    fileTypes: _containers.RepeatedCompositeFieldContainer[FileType]
    id: str
    name: str
    staticTags: _containers.ScalarMap[str, str]
    def __init__(self, id: _Optional[str] = ..., active: bool = ..., name: _Optional[str] = ..., staticTags: _Optional[_Mapping[str, str]] = ..., fileTypes: _Optional[_Iterable[_Union[FileType, _Mapping]]] = ...) -> None: ...

class RecordType(_message.Message):
    __slots__ = ["destinations", "fieldTypes", "id", "name", "recordMatches", "rollback", "successCheck", "upload", "validations"]
    DESTINATIONS_FIELD_NUMBER: _ClassVar[int]
    FIELDTYPES_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    RECORDMATCHES_FIELD_NUMBER: _ClassVar[int]
    ROLLBACK_FIELD_NUMBER: _ClassVar[int]
    SUCCESSCHECK_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONS_FIELD_NUMBER: _ClassVar[int]
    destinations: _containers.RepeatedCompositeFieldContainer[FunctionConfig]
    fieldTypes: _containers.RepeatedCompositeFieldContainer[FieldType]
    id: int
    name: str
    recordMatches: _containers.RepeatedScalarFieldContainer[str]
    rollback: FunctionConfig
    successCheck: FunctionConfig
    upload: FunctionConfig
    validations: _containers.RepeatedCompositeFieldContainer[FunctionConfig]
    def __init__(self, id: _Optional[int] = ..., name: _Optional[str] = ..., recordMatches: _Optional[_Iterable[str]] = ..., fieldTypes: _Optional[_Iterable[_Union[FieldType, _Mapping]]] = ..., successCheck: _Optional[_Union[FunctionConfig, _Mapping]] = ..., upload: _Optional[_Union[FunctionConfig, _Mapping]] = ..., rollback: _Optional[_Union[FunctionConfig, _Mapping]] = ..., validations: _Optional[_Iterable[_Union[FunctionConfig, _Mapping]]] = ..., destinations: _Optional[_Iterable[_Union[FunctionConfig, _Mapping]]] = ...) -> None: ...
