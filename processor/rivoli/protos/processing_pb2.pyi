from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CopyLog(_message.Message):
    __slots__ = ["files", "partnerId", "time"]
    class EvaluatedFile(_message.Message):
        __slots__ = ["fileId", "fileTypeId", "name", "resolution", "sizeBytes"]
        class Resolution(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
            __slots__ = []
        COPIED: CopyLog.EvaluatedFile.Resolution
        FILEID_FIELD_NUMBER: _ClassVar[int]
        FILETYPEID_FIELD_NUMBER: _ClassVar[int]
        FILE_EXISTS: CopyLog.EvaluatedFile.Resolution
        NAME_FIELD_NUMBER: _ClassVar[int]
        NO_MATCH: CopyLog.EvaluatedFile.Resolution
        RESOLUTION_FIELD_NUMBER: _ClassVar[int]
        RESOLUTION_UNKNOWN: CopyLog.EvaluatedFile.Resolution
        SIZEBYTES_FIELD_NUMBER: _ClassVar[int]
        fileId: int
        fileTypeId: str
        name: str
        resolution: CopyLog.EvaluatedFile.Resolution
        sizeBytes: int
        def __init__(self, name: _Optional[str] = ..., sizeBytes: _Optional[int] = ..., resolution: _Optional[_Union[CopyLog.EvaluatedFile.Resolution, str]] = ..., fileTypeId: _Optional[str] = ..., fileId: _Optional[int] = ...) -> None: ...
    FILES_FIELD_NUMBER: _ClassVar[int]
    PARTNERID_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    files: _containers.RepeatedCompositeFieldContainer[CopyLog.EvaluatedFile]
    partnerId: str
    time: int
    def __init__(self, partnerId: _Optional[str] = ..., time: _Optional[int] = ..., files: _Optional[_Iterable[_Union[CopyLog.EvaluatedFile, _Mapping]]] = ...) -> None: ...

class File(_message.Message):
    __slots__ = ["created", "development_file", "fileDate", "fileTypeId", "hash", "headerColumns", "id", "location", "log", "name", "partnerId", "requiresReview", "sizeBytes", "stats", "status", "tags", "times", "updated"]
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class TagsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AGGREGATED: File.Status
    AGGREGATING: File.Status
    COMPLETED: File.Status
    CREATED_FIELD_NUMBER: _ClassVar[int]
    DEVELOPMENT_FILE_FIELD_NUMBER: _ClassVar[int]
    FILEDATE_FIELD_NUMBER: _ClassVar[int]
    FILETYPEID_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    HEADERCOLUMNS_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LOADED: File.Status
    LOADING: File.Status
    LOCATION_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    NEW: File.Status
    PARSED: File.Status
    PARSING: File.Status
    PARTNERID_FIELD_NUMBER: _ClassVar[int]
    REQUIRESREVIEW_FIELD_NUMBER: _ClassVar[int]
    SIZEBYTES_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_UNKNOWN: File.Status
    TAGS_FIELD_NUMBER: _ClassVar[int]
    TIMES_FIELD_NUMBER: _ClassVar[int]
    UPDATED_FIELD_NUMBER: _ClassVar[int]
    UPLOADED: File.Status
    UPLOADING: File.Status
    VALIDATED: File.Status
    VALIDATING: File.Status
    WAITING_APPROVAL_TO_UPLOAD: File.Status
    created: int
    development_file: bool
    fileDate: str
    fileTypeId: str
    hash: bytes
    headerColumns: _containers.RepeatedScalarFieldContainer[str]
    id: int
    location: str
    log: _containers.RepeatedCompositeFieldContainer[ProcessingLog]
    name: str
    partnerId: str
    requiresReview: bool
    sizeBytes: int
    stats: RecordStats
    status: File.Status
    tags: _containers.ScalarMap[str, str]
    times: RecordTimes
    updated: int
    def __init__(self, id: _Optional[int] = ..., partnerId: _Optional[str] = ..., development_file: bool = ..., hash: _Optional[bytes] = ..., sizeBytes: _Optional[int] = ..., name: _Optional[str] = ..., location: _Optional[str] = ..., created: _Optional[int] = ..., updated: _Optional[int] = ..., status: _Optional[_Union[File.Status, str]] = ..., requiresReview: bool = ..., fileTypeId: _Optional[str] = ..., headerColumns: _Optional[_Iterable[str]] = ..., fileDate: _Optional[str] = ..., tags: _Optional[_Mapping[str, str]] = ..., log: _Optional[_Iterable[_Union[ProcessingLog, _Mapping]]] = ..., stats: _Optional[_Union[RecordStats, _Mapping]] = ..., times: _Optional[_Union[RecordTimes, _Mapping]] = ...) -> None: ...

class ProcessingError(_message.Message):
    __slots__ = ["error", "field", "functionId"]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    FIELD_FIELD_NUMBER: _ClassVar[int]
    FUNCTIONID_FIELD_NUMBER: _ClassVar[int]
    error: str
    field: str
    functionId: str
    def __init__(self, field: _Optional[str] = ..., functionId: _Optional[str] = ..., error: _Optional[str] = ...) -> None: ...

class ProcessingLog(_message.Message):
    __slots__ = ["message", "source", "time", "type"]
    class LoggingType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    LOGGINGTYPE_UNKNOWN: ProcessingLog.LoggingType
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SOME_TEXT: ProcessingLog.LoggingType
    SOURCE_FIELD_NUMBER: _ClassVar[int]
    TIME_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    message: str
    source: str
    time: int
    type: ProcessingLog.LoggingType
    def __init__(self, source: _Optional[str] = ..., type: _Optional[_Union[ProcessingLog.LoggingType, str]] = ..., time: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...

class Record(_message.Message):
    __slots__ = ["aggregatedFields", "hash", "id", "log", "parsedFields", "rawColumns", "rawLine", "recordType", "retriable", "sharedKey", "status", "uploadConfirmationId", "uploadError", "validatedFields", "validationErrors", "validationExecutionErrors"]
    class RecordTypeRef(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class Status(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = []
    class AggregatedFieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ParsedFieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    class ValidatedFieldsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    AGGREGATEDFIELDS_FIELD_NUMBER: _ClassVar[int]
    HASH_FIELD_NUMBER: _ClassVar[int]
    HEADER: Record.RecordTypeRef
    ID_FIELD_NUMBER: _ClassVar[int]
    LOADED: Record.Status
    LOAD_ERROR: Record.Status
    LOG_FIELD_NUMBER: _ClassVar[int]
    PARSED: Record.Status
    PARSEDFIELDS_FIELD_NUMBER: _ClassVar[int]
    PARSE_ERROR: Record.Status
    RAWCOLUMNS_FIELD_NUMBER: _ClassVar[int]
    RAWLINE_FIELD_NUMBER: _ClassVar[int]
    RECORDTYPE_FIELD_NUMBER: _ClassVar[int]
    RECORDTYPE_UNKNOWN: Record.RecordTypeRef
    RETRIABLE_FIELD_NUMBER: _ClassVar[int]
    SHAREDKEY_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATUS_UNKNOWN: Record.Status
    UPLOADCONFIRMATIONID_FIELD_NUMBER: _ClassVar[int]
    UPLOADED: Record.Status
    UPLOADERROR_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_ERROR: Record.Status
    VALIDATED: Record.Status
    VALIDATEDFIELDS_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONERRORS_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONEXECUTIONERRORS_FIELD_NUMBER: _ClassVar[int]
    VALIDATION_ERROR: Record.Status
    aggregatedFields: _containers.ScalarMap[str, str]
    hash: bytes
    id: int
    log: _containers.RepeatedCompositeFieldContainer[ProcessingLog]
    parsedFields: _containers.ScalarMap[str, str]
    rawColumns: _containers.RepeatedScalarFieldContainer[str]
    rawLine: str
    recordType: Record.RecordTypeRef
    retriable: bool
    sharedKey: str
    status: Record.Status
    uploadConfirmationId: str
    uploadError: ProcessingError
    validatedFields: _containers.ScalarMap[str, str]
    validationErrors: _containers.RepeatedCompositeFieldContainer[ProcessingError]
    validationExecutionErrors: _containers.RepeatedCompositeFieldContainer[ProcessingError]
    def __init__(self, id: _Optional[int] = ..., hash: _Optional[bytes] = ..., recordType: _Optional[_Union[Record.RecordTypeRef, str]] = ..., status: _Optional[_Union[Record.Status, str]] = ..., retriable: bool = ..., sharedKey: _Optional[str] = ..., rawLine: _Optional[str] = ..., rawColumns: _Optional[_Iterable[str]] = ..., parsedFields: _Optional[_Mapping[str, str]] = ..., validatedFields: _Optional[_Mapping[str, str]] = ..., aggregatedFields: _Optional[_Mapping[str, str]] = ..., log: _Optional[_Iterable[_Union[ProcessingLog, _Mapping]]] = ..., validationErrors: _Optional[_Iterable[_Union[ProcessingError, _Mapping]]] = ..., validationExecutionErrors: _Optional[_Iterable[_Union[ProcessingError, _Mapping]]] = ..., uploadError: _Optional[_Union[ProcessingError, _Mapping]] = ..., uploadConfirmationId: _Optional[str] = ...) -> None: ...

class RecordStats(_message.Message):
    __slots__ = ["approximateRows", "loadedRecordsError", "loadedRecordsSuccess", "parsedRecordsError", "parsedRecordsSuccess", "steps", "totalRows", "uploadedRecordsError", "uploadedRecordsSkipped", "uploadedRecordsSuccess", "validatedRecordsError", "validatedRecordsSuccess", "validationErrors", "validationExecutionErrors"]
    class StepsEntry(_message.Message):
        __slots__ = ["key", "value"]
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: StepStats
        def __init__(self, key: _Optional[str] = ..., value: _Optional[_Union[StepStats, _Mapping]] = ...) -> None: ...
    APPROXIMATEROWS_FIELD_NUMBER: _ClassVar[int]
    LOADEDRECORDSERROR_FIELD_NUMBER: _ClassVar[int]
    LOADEDRECORDSSUCCESS_FIELD_NUMBER: _ClassVar[int]
    PARSEDRECORDSERROR_FIELD_NUMBER: _ClassVar[int]
    PARSEDRECORDSSUCCESS_FIELD_NUMBER: _ClassVar[int]
    STEPS_FIELD_NUMBER: _ClassVar[int]
    TOTALROWS_FIELD_NUMBER: _ClassVar[int]
    UPLOADEDRECORDSERROR_FIELD_NUMBER: _ClassVar[int]
    UPLOADEDRECORDSSKIPPED_FIELD_NUMBER: _ClassVar[int]
    UPLOADEDRECORDSSUCCESS_FIELD_NUMBER: _ClassVar[int]
    VALIDATEDRECORDSERROR_FIELD_NUMBER: _ClassVar[int]
    VALIDATEDRECORDSSUCCESS_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONERRORS_FIELD_NUMBER: _ClassVar[int]
    VALIDATIONEXECUTIONERRORS_FIELD_NUMBER: _ClassVar[int]
    approximateRows: int
    loadedRecordsError: int
    loadedRecordsSuccess: int
    parsedRecordsError: int
    parsedRecordsSuccess: int
    steps: _containers.MessageMap[str, StepStats]
    totalRows: int
    uploadedRecordsError: int
    uploadedRecordsSkipped: int
    uploadedRecordsSuccess: int
    validatedRecordsError: int
    validatedRecordsSuccess: int
    validationErrors: int
    validationExecutionErrors: int
    def __init__(self, approximateRows: _Optional[int] = ..., loadedRecordsSuccess: _Optional[int] = ..., loadedRecordsError: _Optional[int] = ..., totalRows: _Optional[int] = ..., parsedRecordsSuccess: _Optional[int] = ..., parsedRecordsError: _Optional[int] = ..., validatedRecordsSuccess: _Optional[int] = ..., validatedRecordsError: _Optional[int] = ..., validationExecutionErrors: _Optional[int] = ..., validationErrors: _Optional[int] = ..., uploadedRecordsSuccess: _Optional[int] = ..., uploadedRecordsError: _Optional[int] = ..., uploadedRecordsSkipped: _Optional[int] = ..., steps: _Optional[_Mapping[str, StepStats]] = ...) -> None: ...

class RecordTimes(_message.Message):
    __slots__ = ["aggregatingEndTime", "aggregatingStartTime", "loadingEndTime", "loadingStartTime", "parsingEndTime", "parsingStartTime", "uploadingEndTime", "uploadingStartTime", "validatingEndTime", "validatingStartTime"]
    AGGREGATINGENDTIME_FIELD_NUMBER: _ClassVar[int]
    AGGREGATINGSTARTTIME_FIELD_NUMBER: _ClassVar[int]
    LOADINGENDTIME_FIELD_NUMBER: _ClassVar[int]
    LOADINGSTARTTIME_FIELD_NUMBER: _ClassVar[int]
    PARSINGENDTIME_FIELD_NUMBER: _ClassVar[int]
    PARSINGSTARTTIME_FIELD_NUMBER: _ClassVar[int]
    UPLOADINGENDTIME_FIELD_NUMBER: _ClassVar[int]
    UPLOADINGSTARTTIME_FIELD_NUMBER: _ClassVar[int]
    VALIDATINGENDTIME_FIELD_NUMBER: _ClassVar[int]
    VALIDATINGSTARTTIME_FIELD_NUMBER: _ClassVar[int]
    aggregatingEndTime: int
    aggregatingStartTime: int
    loadingEndTime: int
    loadingStartTime: int
    parsingEndTime: int
    parsingStartTime: int
    uploadingEndTime: int
    uploadingStartTime: int
    validatingEndTime: int
    validatingStartTime: int
    def __init__(self, loadingStartTime: _Optional[int] = ..., loadingEndTime: _Optional[int] = ..., parsingStartTime: _Optional[int] = ..., parsingEndTime: _Optional[int] = ..., validatingStartTime: _Optional[int] = ..., validatingEndTime: _Optional[int] = ..., aggregatingStartTime: _Optional[int] = ..., aggregatingEndTime: _Optional[int] = ..., uploadingStartTime: _Optional[int] = ..., uploadingEndTime: _Optional[int] = ...) -> None: ...

class StepStats(_message.Message):
    __slots__ = ["failure", "input", "success"]
    FAILURE_FIELD_NUMBER: _ClassVar[int]
    INPUT_FIELD_NUMBER: _ClassVar[int]
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    failure: int
    input: int
    success: int
    def __init__(self, input: _Optional[int] = ..., success: _Optional[int] = ..., failure: _Optional[int] = ...) -> None: ...
