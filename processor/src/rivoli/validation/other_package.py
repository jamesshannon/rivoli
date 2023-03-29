from rivoli.validation import apis

from rivoli import config
from rivoli import protos


def modify_field_with_uuid(value: str, callservice: protos.CallableService) -> str:
  service = config.get_services_by_ids({callservice.service_id})
  resp = apis.make_request('/uuid', service[callservice.service_id])

  return f'{value} + {resp["uuid"]}'
