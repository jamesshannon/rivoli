""" Protobuf to/from Python dict functions.
Taken from https://github.com/benhodgson/protobuf-to-dict where it is licensed
with the (Un)license

And modified for:
* Support py3
* Use of bytes, rather than b64
* Support for google.proto.struct
* Typing support
"""
from collections import OrderedDict
import typing as t

from google.protobuf.message import Message
from google.protobuf.descriptor import FieldDescriptor, EnumValueDescriptor


__all__ = ["protobuf_to_dict", "TYPE_CALLABLE_MAP", "dict_to_protobuf",
           "REVERSE_TYPE_CALLABLE_MAP"]


EXTENSION_CONTAINER = '___X'

TypeConverter = t.Callable[[t.Any], t.Any]
TypeConverterMap = dict[t.Union[int, str], TypeConverter]

TYPE_CALLABLE_MAP: TypeConverterMap = {
    FieldDescriptor.TYPE_DOUBLE: float,
    FieldDescriptor.TYPE_FLOAT: float,
    FieldDescriptor.TYPE_INT32: int,
    FieldDescriptor.TYPE_INT64: int,
    FieldDescriptor.TYPE_UINT32: int,
    FieldDescriptor.TYPE_UINT64: int,
    FieldDescriptor.TYPE_SINT32: int,
    FieldDescriptor.TYPE_SINT64: int,
    FieldDescriptor.TYPE_FIXED32: int,
    FieldDescriptor.TYPE_FIXED64: int,
    FieldDescriptor.TYPE_SFIXED32: int,
    FieldDescriptor.TYPE_SFIXED64: int,
    FieldDescriptor.TYPE_BOOL: bool,
    FieldDescriptor.TYPE_STRING: str,
    FieldDescriptor.TYPE_BYTES: bytes, #lambda b: b.encode("base64"),
    FieldDescriptor.TYPE_ENUM: int,
}

REVERSE_TYPE_CALLABLE_MAP: TypeConverterMap = {
    #FieldDescriptor.TYPE_BYTES: lambda b: b.decode('base64'),
}

M = t.TypeVar('M', bound=Message)

def repeated(type_callable: TypeConverter
    ) -> t.Callable[[list[t.Any]], list[t.Any]]:
  return lambda value_list: [type_callable(value) for value in value_list]


def enum_label_name(field: FieldDescriptor, value: t.Any):
  return field.enum_type.values_by_number[int(value)].name

def protobuf_to_dict(pb: Message,
    type_callable_map: TypeConverterMap = TYPE_CALLABLE_MAP,
    use_enum_labels: bool = False, ordered: bool = False ) -> dict[str, t.Any]:
  dct_class: type[dict[str, t.Any]] = OrderedDict if ordered else dict
  result_dict: dict[str, t.Any] = dct_class()
  extensions: dict[str, t.Union[TypeConverter, list[TypeConverter]]] = {}

  try:
    if pb.DESCRIPTOR.full_name == 'google.protobuf.Struct':
      return {key: pb.fields[key].string_value for key in pb.fields}

    if pb.DESCRIPTOR.full_name == 'google.protobuf.Timestamp':
      return pb.ToDatetime()

  except AttributeError:
    pass

  for field, value in pb.ListFields():
    if (hasattr(field, 'message_type') and field.message_type
        and field.message_type.has_options
        and field.message_type.GetOptions().map_entry):
      # this is a dict... it can't be adaptored like a message
      dct: dict[str, str] = {}
      for key in value:
        if field.message_type.fields[1].type == FieldDescriptor.TYPE_MESSAGE:
          dct[key] = _get_field_value_adaptor(pb, field, type_callable_map, use_enum_labels)(value[key])
        else:
          dct[key] = str(value[key])

      result_dict[field.name] = dct
      continue

    type_callable = _get_field_value_adaptor(pb, field, type_callable_map,
                                             use_enum_labels)
    if field.label == FieldDescriptor.LABEL_REPEATED:
      type_callable = repeated(type_callable)

    if field.is_extension:
      extensions[str(field.number)] = type_callable(value)
      continue

    result_dict[field.name] = type_callable(value)

  if extensions:
    result_dict[EXTENSION_CONTAINER] = extensions

  return result_dict


def _get_field_value_adaptor(pb: Message, field: FieldDescriptor,
    type_callable_map: TypeConverterMap = TYPE_CALLABLE_MAP,
    use_enum_labels: bool = False) -> TypeConverter:

  if field.type == FieldDescriptor.TYPE_MESSAGE:
    # recursively encode protobuf sub-message
    return lambda pb: protobuf_to_dict(pb,
      type_callable_map=type_callable_map,
      use_enum_labels=use_enum_labels)

  if use_enum_labels and field.type == FieldDescriptor.TYPE_ENUM:
    return lambda value: enum_label_name(field, value)

  # See if the field has any options
  try:
    option = field.GetOptions().ListFields()[0]
    if option[1] is True and option[0].name in type_callable_map:
      return type_callable_map[option[0].name]
  except (IndexError):
    pass

  if field.type in type_callable_map:
    return type_callable_map[field.type]

  raise TypeError("Field %s.%s has unrecognised type id %d" % (
    pb.__class__.__name__, field.name, field.type))


def dict_to_protobuf(pb_klass_or_instance: t.Union[M, type[M]],
  values: dict[str, t.Any],
  type_callable_map: TypeConverterMap = REVERSE_TYPE_CALLABLE_MAP,
  strict: bool = True) -> M:
  """Populates a protobuf model from a dictionary.
  :param pb_klass_or_instance: a protobuf message class, or an protobuf instance
  :type pb_klass_or_instance: a type or instance of a subclass of google.protobuf.message.Message
  :param dict values: a dictionary of values. Repeated and nested values are
      fully supported.
  :param dict type_callable_map: a mapping of protobuf types to callables for setting
      values on the target instance.
  :param bool strict: complain if keys in the map are not fields on the message.
  """
  if isinstance(pb_klass_or_instance, Message):
    instance = pb_klass_or_instance
  else:
    instance = pb_klass_or_instance()

  return _dict_to_protobuf(instance, values, type_callable_map, strict)


def _get_field_mapping(pb: Message, dict_value: dict[str, t.Any],
    strict: bool) -> list[tuple[FieldDescriptor, t.Any, t.Any]]:
  field_mapping: list[tuple[FieldDescriptor, t.Any, t.Any]] = []

  for key, value in dict_value.items():
    if key == EXTENSION_CONTAINER:
      continue

    if pb.DESCRIPTOR.full_name == 'google.protobuf.Struct':
      pb[key] = value
      continue

    if key not in pb.DESCRIPTOR.fields_by_name:
      if strict:
        raise KeyError("%s does not have a field called %s" % (pb, key))
      continue

    field_mapping.append((pb.DESCRIPTOR.fields_by_name[key], value, getattr(pb, key, None)))

  for ext_num, ext_val in dict_value.get(EXTENSION_CONTAINER, {}).items():
    try:
      ext_num = int(ext_num)
    except ValueError:
      raise ValueError("Extension keys must be integers.")
    if ext_num not in pb._extensions_by_number:
      if strict:
        raise KeyError("%s does not have a extension with number %s. Perhaps you forgot to import it?" % (pb, key))
      continue

    ext_field: FieldDescriptor = pb._extensions_by_number[ext_num]
    pb_val = None
    pb_val = pb.Extensions[ext_field]
    field_mapping.append((ext_field, ext_val, pb_val))

  return field_mapping


def _dict_to_protobuf(pb: Message, value: dict[str, t.Any],
    type_callable_map: TypeConverterMap, strict: bool) -> Message:
  fields = _get_field_mapping(pb, value, strict)

  for field, input_value, pb_value in fields:
    if field.label == FieldDescriptor.LABEL_REPEATED:
      for item in input_value:
        if field.type == FieldDescriptor.TYPE_MESSAGE:
          if (hasattr(field, 'message_type') and field.message_type
              and field.message_type.has_options
              and field.message_type.GetOptions().map_entry):

            if type(pb_value).__name__ == 'MessageMapContainer':
              for dct_key, dct_value in input_value.items():
                m = pb_value[dct_key]
                _dict_to_protobuf(m, dct_value, type_callable_map, strict)
            else:
              getattr(pb, field.name)[item] = str(input_value[item])
          else:
            m = pb_value.add()
            _dict_to_protobuf(m, item, type_callable_map, strict)
        elif field.type == FieldDescriptor.TYPE_ENUM and isinstance(item, str):
          pb_value.append(_string_to_enum(field, item))
        else:
          pb_value.append(item)
      continue
    if field.type == FieldDescriptor.TYPE_MESSAGE:
      _dict_to_protobuf(pb_value, input_value, type_callable_map, strict)
      continue

    if field.type in type_callable_map:
      input_value = type_callable_map[field.type](input_value)

    elif type(input_value).__name__ in type_callable_map:
      input_value = type_callable_map[type(input_value).__name__](input_value)

    if field.is_extension:
      pb.Extensions[field] = input_value
      continue

    if field.type == FieldDescriptor.TYPE_ENUM and isinstance(input_value, str):
      input_value = _string_to_enum(field, input_value)

    setattr(pb, field.name, input_value)

  return pb

def _string_to_enum(field: FieldDescriptor, input_value: str) -> int:
  enum_dict: dict[str, EnumValueDescriptor] = field.enum_type.values_by_name
  try:
    input_value: int = enum_dict[input_value].number
  except KeyError:
    raise KeyError("`%s` is not a valid value for field `%s`" %
                   (input_value, field.name))
  return input_value
