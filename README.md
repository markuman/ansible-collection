# markuman.inwx

This is my fork of [inwx.collection](https://github.com/inwx/ansible-collection).

Using my fork, you must use `markuman.inwx.dns` and `markuman.inwx.session`. Therefore you can use both collections in parallel.

Install from github

```
ansible-galaxy collection install git+https://github.com/markuman/inwx.collection.git
```

## Differences between official collection an my fork

* Deleting record not working? [#20](https://github.com/inwx/ansible-collection/issues/20)
  * https://github.com/inwx/ansible-collection/pull/23
* add support for `https` record type
  * https://github.com/inwx/ansible-collection/pull/24

## others

* remove duplicated APIClass code
  * use `pip install inwx-domrobot` as depencencies for both modules.
* Add partiell diff support when running `ansible-playbook ... --diff`

```
TASK [create a record] **********************************************************
--- before
+++ after
@@ -1 +1,6 @@
-[]
+- content: 127.0.0.123
+  id: 1442086446
+  name: nureintest.osuv.de
+  priority: 0
+  ttl: 300
+  type: A

changed: [localhost]

TASK [delete a record] **********************************************************
--- before
+++ after
@@ -1,6 +1 @@
-- content: 127.0.0.123
-  id: 1442086446
-  name: nureintest.osuv.de
-  priority: 0
-  ttl: 300
-  type: A
+[]

changed: [localhost]
```

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