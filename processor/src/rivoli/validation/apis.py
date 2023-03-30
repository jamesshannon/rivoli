""" Module to help validators make API requests. """
import requests

from rivoli import protos

# TODO: Create a session and request pooling
# But first figure out that will leak or cookies

# create a higher-level function to capture errors and convert into validation
# errors

def make_request(path: str, service: protos.Service) -> dict[str, str]:
  url = f'https://{service.hostname}{path}'
  resp = requests.get(url, timeout=10)
  return resp.json()

