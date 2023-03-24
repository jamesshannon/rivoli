""" Validator stuff. """
import typing as t

BasicTypes = t.Union[int, str]

class Validator(t.Protocol):
  """ Validator function signature. """
  def __call__(self, value: BasicTypes) -> BasicTypes: ...
