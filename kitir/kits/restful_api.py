# Standard Imports
import itertools
import json

# kitir Imports
from kitir import *

# External Imports
import requests

log = logging.getLogger('kitir.kits.restful_api')
# disable annoying debug logs from urllib3.connectionpool
urllib_log = logging.getLogger('urllib3.connectionpool')
urllib_log.setLevel(logging.WARN)


class RestfulAPI(object):
    """
    A class which wraps the process of sending restful API requests using the requests package
    conveniently logs all transactions for debugging and provides extendability
    """
    # todo: add extendability and convenience

    # class constants
    # transaction counter as a class constant is useful to prevent clashes with the same id
    transaction_counter = itertools.count()
    # the request timeout helps prevent hanging
    request_timeout = 120
    # these strings/keys are used to help parse kwargs related to logging transactions out of regular kwargs
    _log_keys = [
        '_log_transact_id',
        '_log_transact_name',
        '_log_save_request',
        '_log_save_response',
        '_log_dir_request',
        '_log_dir_response',
    ]
    # default log paths
    _cls_log_dir = ir_log_dir  # you should override this in your inheritors
    _cls_request_dir = _cls_log_dir + '/request'
    _cls_response_dir = _cls_log_dir + '/response'
    # errors that should be ignored when converting JSON data
    _ignored_json_convert_error_messages = [
        'Extra data',
        'No JSON object could be decoded',
        "Expecting value"
    ]
    # this file format is here so it can be extended easily
    _format_counter_id = '{id:03}'
    _format_log_file_path = '{directory}/{transaction_id}.txt'

    def __init__(self, base_url, **kwargs):
        self.base_url = base_url
        self.name = kwargs.pop('name', 'rest')
        self.log_rest_dir = kwargs.pop('log_rest_dir', os.path.join(self._cls_log_dir, self.name))
        self.session = requests.session()

    @property
    def request_data_dir(self):
        """directory to store request data and logs"""
        return os.path.join(self.log_rest_dir, 'request')

    @property
    def response_data_dir(self):
        """directory to store response data and logs"""
        return os.path.join(self.log_rest_dir, 'response')

    def __add_default_log_dirs_to_kwargs(self, kwargs):
        kwargs.setdefault('_log_dir_request', self.request_data_dir)
        kwargs.setdefault('_log_dir_response', self.response_data_dir)

    @classmethod
    def _get_log_request_file_path(cls, directory, transact_id):
        """creates the final file path for request logs"""
        return cls._format_log_file_path.format(directory=directory, transaction_id=transact_id)

    @classmethod
    def _get_log_response_file_path(cls, directory, transact_id):
        """creates the final file path for response logs"""
        return cls._format_log_file_path.format(directory=directory, transaction_id=transact_id)

    @classmethod
    def _get_next_id_from_counter(cls, id_frmt=None):
        id_frmt = id_frmt or cls._format_counter_id
        return id_frmt.format(id=next(cls.transaction_counter))

    @classmethod
    def _get_transaction_id_parts(cls):
        """gets the parts to include in the transaction id (log file name)"""
        return [cls._get_next_id_from_counter()]

    @classmethod
    def _make_transaction_id(cls, *args):
        """construct the transaction id using the default parts and any args"""
        return '.'.join(map(str, filter(None, cls._get_transaction_id_parts() + list(args))))

    def make_transaction_id(self, *args):
        return self._make_transaction_id(*args)

    @classmethod
    def _extract_log_kwargs(cls, **kwargs):
        """extracts the log kwargs from request kwargs for use in logging"""
        log_kwargs = {lk[5:]: kwargs.pop(lk) for lk in cls._log_keys if lk in kwargs.keys()}
        return log_kwargs, kwargs

    @classmethod
    def _log_transaction(cls, response, **kwargs):
        """
        logs the request transaction, both request and response with optional kwargs
        :param response:
        :param kwargs:
        :return:
        """
        transact_name = kwargs.pop('transact_name', None)
        transact_parts = [transact_name, response.request.method]
        transact_id = kwargs.pop('transact_id', None) or cls._make_transaction_id(*transact_parts)
        save_request = kwargs.pop('save_request', True)
        save_response = kwargs.pop('save_response', True)
        dir_request = kwargs.pop('dir_request', cls._cls_request_dir)
        dir_response = kwargs.pop('dir_response', cls._cls_response_dir)
        if save_request:
            try:
                request_file_path = cls._get_log_request_file_path(dir_request, transact_id)
                cls._log_request(response, request_file_path)
            except Exception as exc:
                log.error('Exception logging rest transaction request: id={} exc={} trace...'.format(transact_id, exc),
                          exc_info=True)
        if save_response:
            try:
                response_file_path = cls._get_log_response_file_path(dir_response, transact_id)
                cls._log_response(response, response_file_path)
            except Exception as exc:
                log.error('Exception logging rest transaction response: id={} exc={} trace...'.format(transact_id, exc),
                          exc_info=True)

    @classmethod
    def _log_request(cls, response, request_file_path):
        """log the request side of a transaction"""
        if response.request.body:
            content = response.request.body
        else:
            content = response.request.url
        data_file = utils.write_file(request_file_path, content)
        log.trace('log-request: method={} url={} path={} data={}'.format(
            response.request.method, response.request.url, data_file, bool(response.request.body)))

    @classmethod
    def _log_response(cls, response, response_file_path):
        """log the response side of a transaction"""
        content = cls._get_content_from_json(response)
        if content is not None:
            data_file = utils.write_file(response_file_path, content)
            log.trace('log-response: status={} data={}'.format(response.status_code, data_file))
        else:
            log.trace('log-response: status={} data=None'.format(response.status_code))

    @classmethod
    def _get_content_from_json(cls, response):
        """attempts to extract content from a json in the response from server"""
        try:
            content = response.json()
        # except json.JSONDecodeError as jde:
        #
        except ValueError as vexc:
            if not any([ignored_msg in str(vexc) for ignored_msg in cls._ignored_json_convert_error_messages]):
                raise
            elif response.content:
                content = response.content
            else:
                content = None
        else:
            content = json.dumps(content, indent=4)
        return content

    @classmethod
    def _request_get(cls, url, **kwargs):
        """sends a GET command using requests package"""
        ignore_request_timeout = kwargs.pop('ignore_request_timeout', False)
        ignore_connection_aborted = kwargs.pop('ignore_connection_aborted', False)
        log_action = kwargs.pop('log_action', True)
        session = kwargs.pop('session', None)
        kwargs.setdefault('timeout', cls.request_timeout)
        log_kwargs, kwargs = cls._extract_log_kwargs(**kwargs)
        if log_action:
            log.debug('request.get: url={}'.format(url))
        try:
            if session:
                r = session.get(url, **kwargs)
            else:
                r = requests.get(url, **kwargs)
        except requests.ReadTimeout as exc:
            if ignore_request_timeout:
                log.debug('Requests Timeout, ignored: url={} exc={}'.format(url, exc))
            else:
                raise
        except requests.ConnectionError as exc:
            if ignore_connection_aborted and 'Connection aborted.' in str(exc):
                log.debug('Connection Aborted, ignored: url={} exc={}'.format(url, exc))
            else:
                raise
        except requests.RequestException as exc:
            log.error('requests get exception: exc={} url={}'.format(exc, url))
            raise
        else:
            cls._log_transaction(r, **log_kwargs)
            return r

    def request_get(self, url, **kwargs):
        """sends a GET command using requests package"""
        self.__add_default_log_dirs_to_kwargs(kwargs)
        kwargs.setdefault('session', self.session)
        return self._request_get(url, **kwargs)

    @classmethod
    def _request_post(cls, url, **kwargs):
        """sends a POST command using requests package"""
        log_action = kwargs.pop('log_action', True)
        session = kwargs.pop('session', None)
        kwargs.setdefault('timeout', cls.request_timeout)
        log_kwargs, kwargs = cls._extract_log_kwargs(**kwargs)
        if log_action:
            log.debug('request.post: url={}'.format(url))
        try:
            if session:
                r = session.post(url, **kwargs)
            else:
                r = requests.post(url, **kwargs)
        except requests.RequestException as exc:
            log.error('requests post exception: exc={} url={}'.format(exc, url))
            raise
        else:
            cls._log_transaction(r, **log_kwargs)
        return r

    def request_post(self, url, **kwargs):
        """sends a POST command using requests package"""
        self.__add_default_log_dirs_to_kwargs(kwargs)
        kwargs.setdefault('session', self.session)
        return self._request_post(url, **kwargs)

    @classmethod
    def _request_put(cls, url, **kwargs):
        """sends a PUT command using requests package"""
        log_action = kwargs.pop('log_action', True)
        session = kwargs.pop('session', None)
        kwargs.setdefault('timeout', cls.request_timeout)
        log_kwargs, kwargs = cls._extract_log_kwargs(**kwargs)
        if log_action:
            log.debug('request.put: url={}'.format(url))
        try:
            if session:
                r = session.put(url, **kwargs)
            else:
                r = requests.put(url, **kwargs)
        except requests.RequestException as exc:
            log.error('requests put exception: exc={} url={}'.format(exc, url))
            raise
        else:
            cls._log_transaction(r, **log_kwargs)
        return r

    def request_put(self, url, **kwargs):
        """sends a PUT command using requests package"""
        self.__add_default_log_dirs_to_kwargs(kwargs)
        kwargs.setdefault('session', self.session)
        return self._request_put(url, **kwargs)

    @classmethod
    def _request_patch(cls, url, **kwargs):
        """sends a PATCH command using requests package"""
        log_action = kwargs.pop('log_action', True)
        session = kwargs.pop('session', None)
        kwargs.setdefault('timeout', cls.request_timeout)
        log_kwargs, kwargs = cls._extract_log_kwargs(**kwargs)
        if log_action:
            log.debug('request.patch: url={}'.format(url))
        try:
            if session:
                r = session.patch(url, **kwargs)
            else:
                r = requests.patch(url, **kwargs)
        except requests.RequestException as exc:
            log.error('requests patch exception: exc={} url={}'.format(exc, url))
            raise
        else:
            cls._log_transaction(r, **log_kwargs)
        return r

    def request_patch(self, url, **kwargs):
        """sends a PATCH command using requests package"""
        self.__add_default_log_dirs_to_kwargs(kwargs)
        kwargs.setdefault('session', self.session)
        return self._request_patch(url, **kwargs)

    @classmethod
    def _request_delete(cls, url, **kwargs):
        """sends a DELETE command using requests package"""
        log_action = kwargs.pop('log_action', True)
        session = kwargs.pop('session', None)
        kwargs.setdefault('timeout', cls.request_timeout)
        log_kwargs, kwargs = cls._extract_log_kwargs(**kwargs)
        if log_action:
            log.debug('request.delete: url={}'.format(url))
        try:
            if session:
                r = session.delete(url, **kwargs)
            else:
                r = requests.delete(url, **kwargs)
        except requests.RequestException as exc:
            log.error('requests delete exception: exc={} url={}'.format(exc, url))
            raise
        else:
            cls._log_transaction(r, **log_kwargs)
        return r

    def request_delete(self, url, **kwargs):
        """sends a DELETE command using requests package"""
        self.__add_default_log_dirs_to_kwargs(kwargs)
        kwargs.setdefault('session', self.session)
        return self._request_delete(url, **kwargs)
