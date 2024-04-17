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
    tfa_token:
        description:
            - Current time-based 2fa code (totp).
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
    tfa_token: 123456

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
from INWX.Domrobot import ApiClient
from INWX.Domrobot import ApiType

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


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            api_env=dict(type='str', reduired=False, default='live', choices=['live', 'ote']),
            username=dict(type='str', required=True, aliases=['user'], no_log=True),
            password=dict(type='str', required=True, aliases=['pass'], no_log=True),
            tfa_token=dict(type='int', required=False, no_log=True),
        ),
        supports_check_mode=True
    )

    if str(module.params['api_env']) == 'live':
        api_url = ApiClient.API_LIVE_URL
    else:
        api_url = ApiClient.API_OTE_URL

    client = ApiClient(api_url=api_url, api_type=ApiType.JSON_RPC, debug_mode=True)

    login_result = client.login(str(module.params['username']), str(module.params['password']),
                                tfa_token=str(module.params['tfa_token']))

    if login_result['code'] != 1000:
        module.fail_json(msg='API error.', result={'api_response': login_result})
        return None

    # domrobot = session key
    module.exit_json(changed=False, result={'session': client.api_session.cookies.get('domrobot')})


def main():
    run_module()


if __name__ == '__main__':
    main()
