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
                request.path = name
                result = yield from func(*args, **kwargs)
            return result

        return inner
    return outer


def _gen_request_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))


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
            request.path = req.path
            result = yield from handler(req)
        return result

    return middleware


__all__ = ["job_context", "context_middleware_factory"]