import sys
import logging
from logging.handlers import SysLogHandler

from aiolocals.middleware import request


class RequestIdLoggingFilter(logging.Filter):
    """
    A filter that adds the request_id and request_path attributes to the record, if available.
    """
    def filter(self, record):
        try:
            record.request_id = '' if not request.id else request.id
            # record.request_path = '' if not request.path else request.path
        except (AttributeError, ValueError):
            # likely not initialized yet
            record.request_id = ''
            # record.request_path = ''
        return True


def _find_service_name():
    import setproctitle
    service_name = setproctitle.getproctitle()
    bracket_pos = service_name.find("[")
    if bracket_pos > -1:
        service_name = service_name[bracket_pos + 1:service_name.find("]")]
    if len(service_name) > 10:
        service_name = service_name[-25:]
    return service_name


class LogConfiguration:
    """
    Inherit from this class and then pass the instance of inheritor
    to adjust logging configuration for your asyncio application
    """

    format = "{}: [%(request_path)s#%(request_id)s] %(levelname)s - %(message)s"
    """
    The expression which should be used as format of the sole logging formatter.
    """
    name = None
    """
    The name of the service. Defaults to the first paraemter of :func:configure_logging(),
    or process title if None passed
    """

    def get_formatter(self):
        """
        Override this method to get your specific formatter to be in use for the app.
        For example, for logging the time of time format in UTC:

        .. code::

            class MyFormatter(logging.Formatter):

                converter = time.gmtime


            class MyLogConf(LogConfiguration):

                def get_formatter(self):
                    return MyFormatter(fmt=self.format.format(self.name))

        """
        return logging.Formatter(fmt=self.format.format(self.name))

    def get_logging_level(self, debug):
        """
        Override me to use your specific log level, depending on application debug mode.
        """
        return logging.DEBUG if debug else logging.INFO

    def get_filters(self):
        """
        This should return iterable of logging.Filter subclasses, which will be used
        """
        return RequestIdLoggingFilter(),

    def get_log_handler(self, debug):
        """
        This should return logging handler instance.
        """
        handler = logging.StreamHandler(sys.stdout) if debug else \
            SysLogHandler(facility=SysLogHandler.LOG_LOCAL3, address="/dev/log")
        return handler


def configure_logging(service_name, debug=True, logconf=None):
    """
    Configure logging with service name.
    Should be called one time when the service starts.

    :param service_name: The service name to prefix the logs with
    :param debug: Whether to configure debug logging or not
    :param logconf: The LogConfiguration inheritor which is capable of providing interface for
     initialization of common logging configuration bits.
    :type logconf: aiolocals.log.LogConfiguration
    """

    if not service_name:
        service_name = _find_service_name()
    if not logconf:
        logconf = LogConfiguration()
    if not logconf.name:
        logconf.name = service_name
    root_logger = logging.getLogger()
    log_level = logconf.get_logging_level(debug)
    log_handler = logconf.get_log_handler(debug)
    for flt in logconf.get_filters():
        log_handler.addFilter(flt)
    log_handler.setFormatter(logconf.get_formatter())
    root_logger.setLevel(log_level)
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    root_logger.addHandler(log_handler)


__all__ = ["configure_logging", "RequestIdLoggingFilter", "LogConfiguration"]
