""" Validation & Modification types
Function types (e.g., FIELD_VALIDATION, RECORD_VALIDATION) have varying
input/output types. For example, a FIELD_VALIDATION function should always
return the value of that particular field while RECORD_VALIDATION can
return a dict, a Record, or None. We define all of that here.
"""
import typing as t

from rivoli.function_helpers import helpers

# FIELD_VALIDATION
ValFieldInput = str
""" FIELD_VALIDATION input """
ValFieldReturn = str
""" FIELD_VALIDATION return value """

# RECORD_VALIDATION
ValRecordInput = helpers.Record
""" RECORD_VALIDATION input """
ValRecordReturn = t.Optional[t.Union[dict[str, str], helpers.Record]]
""" RECORD_VALIDATION return value """

# RECORD_UPLOAD
UploadRecordInput = helpers.Record
""" RECORD_UPLOAD input """
UploadRecordReturn = str
""" RECORD_UPLOAD return value """

# RECORD_UPLOAD_BATCH
UploadBatchRecordInput = list[helpers.Record]
""" RECORD_UPLOAD_BATCH input """
UploadBatchRecordReturn = str
""" RECORD_UPLOAD_BATCH return value """

# Any validation function -- either FIELD_VALIDATION or RECORD_VALIDATION
ValInput = t.Union[ValFieldInput, ValRecordInput]
""" *_VALIDATION input """
ValReturn = t.Union[ValFieldReturn, ValRecordReturn]
""" *_VALIDATION return value """

# This dict contains tuples of class types for a type alias. It is basically
# a duplicate of the type alias definitions above.
# Python doesn't allow for testing against type aliases, nor can we inspect
# and deconstruct the alias ourselves, so this has to be maintained separately.
CLASS_TUPLES: dict[type, t.Tuple[type, ...]] = {
    ValRecordReturn: (dict, helpers.Record, type(None)),
}

def is_typing_instance(obj: object, type_: type) -> bool:
  """ Return whether object is instance of any class in a type alias.  """
  types = CLASS_TUPLES.get(type_, (type_, ))
  return isinstance(obj, types)
