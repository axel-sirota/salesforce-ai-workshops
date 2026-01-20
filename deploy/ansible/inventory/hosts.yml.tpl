# Template - replace SERVER_IP with terraform output
all:
  hosts:
    workshop:
      ansible_host: SERVER_IP
      ansible_user: root
  vars:
    workshop_domain: "{{ ansible_host }}"
    htpasswd_user: workshop
    htpasswd_password: salesforce2025
