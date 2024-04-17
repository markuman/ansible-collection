# markuman.inwx

This is my fork of [inwx.collection](https://github.com/inwx/ansible-collection).

## Differences between official collection an my fork

* Deleting record not working? [#20](https://github.com/inwx/ansible-collection/issues/20)
  * https://github.com/inwx/ansible-collection/pull/23
* add support for `https` record type
  * https://github.com/inwx/ansible-collection/pull/24

## others

* Add partiell diff support
* `markuman.inwx.session` does not work anymore with the shared secret. instead of, you must pass directly the valid totp value to the module

```yml
- name: totp source. can be any other password manager or self-crafted MFA Vault.
  command: "oathtool -b --totp {{lookup('community.general.keyring', 'totp inwx') }}"
  register: totp

- name: Retrieve session for account with two factor authentication
  markuman.inwx.session:
    username: 'user'
    password: 'pass'
    totp: "{{ totp.stdout }}"
   register: temp_session_output

- name: Ensure A record 'test' exists with prefetched API session
  markuman.inwx.dns:
    domain: osuv.de
    type: A
    ttl: 300
    record: nureintest
    value: "127.0.0.123"
    session: '{{ temp_session_output.result.session }}'