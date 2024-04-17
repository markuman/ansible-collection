#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022, INWX <developer@inwx.de>
# MIT License (see https://opensource.org/licenses/MIT)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: inwx.collection.dns
author:
    - Nick Ufer (@NickUfer)
requirements:
  - python >= 3.6
version_added: "2.10"
short_description: Retrieves an INWX API session with two factor authentication
notes:
    - "This module does NOT support two factor authentication due to excessive rebuilding of the API client and one time use of an OTP."
description:
    - "Retrieves an INWX API session with two factor authentication."
options:
    api_env:
        description:
            - Defines which api should be used.
        type: str
        choices: [ live, ote ]
        default: 'live'
        required: false
    password:
        description:
            - INWX Account Password
            - Required for API authentication.
        type: str
        required: true
        aliases: [ pass ]
    totp:
        description:
            - totp.
        type: str
        required: false
    username:
        description:
            - INWX Account Username
            - Required for API authentication.
        type: str
        required: true
        aliases: [ user ]
'''

EXAMPLES = '''
- name: Get a session without two factor authentication
  inwx.collection.session:
    username: test_user
    password: test_password

- name: Get a session with two factor authentication
  inwx.collection.session:
    username: test_user
    password: test_password
    totp: 123456

- name: Get a session for the OTE API
  inwx.collection.session:
    api_env: 'ote'
    username: test_user
    password: test_password
'''

RETURN = '''
session:
    description: The session for this log in.
    returned: success
    type: str
'''

from ansible.module_utils.basic import AnsibleModule

import json
import random
import string
import struct
import sys
import time

# The requests may not be installed.
# We check that further in the run_module function and install it if necessary
try:
    import requests
except ImportError:
    pass

if sys.version_info.major == 3:
    import xmlrpc.client
else:
    import xmlrpclib


class ApiType:
    XML_RPC = '/xmlrpc/'
    JSON_RPC = '/jsonrpc/'

    def __init__(self):
        pass


class ApiClient:
    CLIENT_VERSION = '3.1.1'
    API_LIVE_URL = 'https://api.domrobot.com'
    API_OTE_URL = 'https://api.ote.domrobot.com'

    def __init__(self, api_url=API_OTE_URL, api_type=ApiType.XML_RPC, language='en', client_transaction_id=None,
                 debug_mode=False):
        """
        Args:
            api_url: Url of the api.
            api_type: Type of the api. See ApiType class for all types.
            language: Language for api messages and error codes in responses.
            client_transaction_id: Sent with every request to distinguish your api requests in case you need support.
            debug_mode: Whether requests and responses should be printed out.
        """

        self.api_url = api_url
        self.api_type = api_type
        self.language = language
        self.client_transaction_id = client_transaction_id
        self.debug_mode = debug_mode
        self.customer = None
        self.api_session = requests.Session()

    def login(self, username, password, totp=None):
        """Performs a login at the api and saves the session cookie for following api calls.

        Args:
            username: Your username.
            password: Your password.
            totp: 123456
        Returns:
            The api response body parsed as a dict.
        Raises:
            Exception: Username, password and totp must not be None.
        """

        if username is None or password is None or totp is None:
            raise Exception('Username, password and totp must not be None.')

        params = {
            'lang': self.language,
            'user': username,
            'pass': password
        }

        login_result = self.call_api('account.login', params)
        if login_result['code'] == 1000 and 'tfa' in login_result['resData'] and login_result['resData']['tfa'] != '0':
            unlock_result = self.call_api('account.unlock', {'tan': totp})
            if unlock_result['code'] != 1000:
                return unlock_result

        return login_result

    def logout(self):
        """Logs out the user and destroys the session.

        Returns:
            The api response body parsed as a dict.
        """

        logout_result = self.call_api('account.logout')
        self.api_session.close()
        self.api_session = requests.Session()
        return logout_result

    def call_api(self, api_method, method_params=None):
        """Makes an api call.

        Args:
            api_method: The name of the method called in the api.
            method_params: A dict of parameters added to the request.
        Returns:
            The api response body parsed as a dict.
        Raises:
            Exception: Api method must not be None.
            Exception: Invalid ApiType.
        """

        if api_method is None:
            raise Exception('Api method must not be None.')
        if method_params is None:
            method_params = {}

        if self.customer:
            method_params['subuser'] = self.customer
        if self.client_transaction_id is not None:
            method_params['clTRID'] = self.client_transaction_id

        if self.api_type == ApiType.XML_RPC:
            if sys.version_info.major == 3:
                payload = xmlrpc.client.dumps((method_params,), api_method, encoding='UTF-8').replace('\n', '')
            else:
                payload = xmlrpclib.dumps((method_params,), api_method, encoding='UTF-8').replace('\n', '')
        elif self.api_type == ApiType.JSON_RPC:
            payload = str(json.dumps({'method': api_method, 'params': method_params}))
        else:
            raise Exception('Invalid ApiType.')

        headers = {
            'Content-Type': 'text/xml; charset=UTF-8',
            'User-Agent': 'DomRobot/' + ApiClient.CLIENT_VERSION + ' (Python ' + self.get_python_version() + ')'
        }

        response = self.api_session.post(self.api_url + self.api_type, data=payload.encode('UTF-8'),
                                         headers=headers)
        response.raise_for_status()

        if self.debug_mode:
            print('Request (' + api_method + '): ' + payload)
            print('Response (' + api_method + '): ' + response.text)

        if self.api_type == ApiType.XML_RPC:
            if sys.version_info.major == 3:
                return xmlrpc.client.loads(response.text)[0][0]
            else:
                return xmlrpclib.loads(response.text)[0][0]
        elif self.api_type == ApiType.JSON_RPC:
            return response.json()

    @staticmethod
    def get_python_version():
        return '.'.join(tuple(str(x) for x in sys.version_info))


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            api_env=dict(type='str', reduired=False, default='live', choices=['live', 'ote']),
            username=dict(type='str', required=True, aliases=['user'], no_log=True),
            password=dict(type='str', required=True, aliases=['pass'], no_log=True),
            totp=dict(type='int', required=False, no_log=True),
        ),
        supports_check_mode=True
    )

    if str(module.params['api_env']) == 'live':
        api_url = ApiClient.API_LIVE_URL
    else:
        api_url = ApiClient.API_OTE_URL

    client = ApiClient(api_url=api_url, api_type=ApiType.JSON_RPC, debug_mode=True)

    login_result = client.login(str(module.params['username']), str(module.params['password']),
                                module.params['totp'])

    if login_result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': login_result})
        return None

    # domrobot = session key
    module.exit_json(changed=False, result={'session': client.api_session.cookies.get('domrobot')})


def main():
    run_module()


if __name__ == '__main__':
    main()
