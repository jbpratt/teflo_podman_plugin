# teflo podman provisioner plugin POC

The Podman provisioner will utilize the executable found or specified and
provision the defined container. For executing Ansible playbooks, the
`ansible_params` setting `ansible_connection` should be set to `podman`, which
utilizes the `containers.podman` collection containing a `podman` connection.
This is similar to using ssh as your connection. Remote podman requires an ssh
connection to the server and Podman configured on the server machine according
to the
[docs](https://github.com/containers/podman/blob/59236762eca31a20d886837698db58e259a21de5/docs/tutorials/remote_client.md)


## Installing

```
pip install git@gitlab.cee.redhat.com:bpratt/teflo_podman_plugin.git
```

## Utilizing

```yaml
---
name: example
description: an example of using the podman provisioner

provision:
  - name: test_driver
    provisioner: podman
    groups:
      - test_drivers
    image: "fedora"
    network_mode: "host"
    privileged: true
    remove: true
    tty: true
    # remote:
    #   user: jbpratt
    #   identity: "{{ HOME }}/.ssh/id_rsa"
    #   uri: ssh://jbpratt@desktop/run/user/1000/podman/podman.sock
    volumes:
      - "{{ PWD }}/:/tests"
    ports:
      - "8080:80/tcp"
    ansible_params:
      ansible_connection: podman
    environment:
      - "SOMEVAR=helloworld"
```
