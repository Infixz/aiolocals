import datetime
import time
import uuid
import asyncio
from functools import wraps
import logging
import random
import string
from .local import Local, Context


request = Local()
"""
A task-local variable to track request 'id' and 'path'
"""


log = logging.getLogger(__name__)


def job_context(name):
    """
    Wraps the execution of a job by setting the request id to something meaningful, allowing tracking of all
    logging statements throughout the job execution.  The request id will start with "JOB"

    :param name: The name of the job for the logs
    :type name: str
    """

    def outer(func):

        @wraps(func)
        @asyncio.coroutine
        def inner(*args, **kwargs):

            with Context(locals=[request]):
                request.id = "JOB" + _gen_request_id()
                # request.path = name
                result = yield from func(*args, **kwargs)
            return result

        return inner
    return outer


_ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase


def basex_encode(num):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    assert(num >= 0)
    if num == 0:
        return _ALPHABET[0]
    arr = []
    base = len(_ALPHABET)
    while num:
        rem = num % base
        num //= base
        arr.append(_ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)


class Id64Generator:

    def __init__(self, date_str):
        self.since = time.mktime(
            datetime.datetime.strptime(date_str, '%Y-%m-%d').timetuple()) * 1000

    def __time_since(self):
        time_since = int(time.time() * 1000 - self.since)
        return time_since

    def gen_id(self):
        return basex_encode((self.__time_since() << 23)
                            + random.SystemRandom().getrandbits(23),
                            )

_id64gen = Id64Generator('2013-01-30')


def _gen_request_id():
    return _id64gen.gen_id()


@asyncio.coroutine
def context_middleware_factory(app, handler):
    """
    A aiohttp middleware factory for wrapping each request with id/path information in task-local variable

    :param app: The aiohttp app
    :type app: aiohttp.web.Application
    :param handler: The next middleware handler
    :type handler: function
    """
    @asyncio.coroutine
    def middleware(req):
        """
        :type request: aiohttp.web.Request
        """

        with Context(locals=[request]):
            request_id = req.headers.get('X-REQUEST-ID')
            if not request_id:
                request_id = "REQ" + _gen_request_id()
            request.id = request_id
            # request.path = req.path
            result = yield from handler(req)
        return result

    return middleware


__all__ = ["job_context", "context_middleware_factory"]