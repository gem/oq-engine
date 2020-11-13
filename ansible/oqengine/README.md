Ansible Role: oqengine
=========

Installs oq-engine from pypip on CentOS 7,8 or Ubuntu 1804, 2004.

The Role first of all check if on the system there is installed python and if the version the installed version is not the 3.8 it setup the python virtual environment on the system using python3.8 that is installed using the follow repository:

- CentOS 7: CentOS SCLo RH
- CentOS 8: PowerTools 
- Ubuntu 1804: Universe
- Ubuntu 2004: python3.8 is the default version 

Role also create the user openquake and generated the ssh keys for this user and the virtual environment of oq engine will be created for user openquake

Requirements
------------

**Ansible 2.9** or later. (NOTE: it might be possible to use earlier versions, in case of issues please try updating Ansible to 2.9+)

**Openssh-server** to have ssh-keygen for creation of ssh key for user openquake 

This role requires root access, so either run it in a playbook with a global become: yes, or invoke the role in your playbook like:

    - hosts: server
      become: yes
      order: sorted

      roles:
        - oqengine

You can use the option sorted as you prefer if you don't want that ansible will play the hosts in the order they were mentioned in the inventory file

Role Variables
--------------
Available variables are listed below, along with default values (see defaults/main.yml):

- The version of the engine that is installed
    
    ```
    engine_release: "3.10.0"
    ```
    
- The requirement file for the engine 
 
     ```
    req_py38: https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt
    ```
    
- The setting of the virtual environment that is used

    ```
    venv_dir: /opt/openquake
    venv_bin: "{{ venv_dir }}/bin"
    ```
    
Dependencies
------------

None.

Example Playbook
----------------

Example playbook of how to use your role to install the oq engine.

Inventory file example for defition of the servers section.

    [servers]
    192.168.22.21 vm_name=vm-centos-7-01
    192.168.22.22 vm_name=vm-centos-8-02
    192.168.22.23 vm_name=vm-ubuntu-1804-01
    [databases]
    192.168.22.24 vm_name=vm-ubuntu-2004-01
    [web-server]
    192.168.22.25 vm_name=vm-centos-8-03
    192.168.22.26 vm_name=vm-centos-8-04
    
The playbook to use:

    - hosts: servers
      become: yes
      roles:
        - oqengine
        
Inside vars/main.yml:

    engine_release: "3.10.0"
    req_py38: https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt
    venv_dir: /opt/openquake
    venv_bin: "{{ venv_dir }}/bin"
    
Use also pre_tasks to assure to update the cache for Ubuntu derivate

      pre_tasks:
        - name: Update apt cache.
          apt:
            update_cache: true
            cache_valid_time: 600
          when: ansible_os_family == 'Ubuntu'

To have the follow playbook:

        - hosts: servers
          become: yes
          roles:
            - oqengine

          pre_tasks:
             - name: Update apt cache.
               apt:
                 update_cache: true
                 cache_valid_time: 600
               when: ansible_os_family == 'Ubuntu'


License
-------

AGPL3
