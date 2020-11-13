Ansible Role: oqengine
======================

Installs the OpenQuake engine on CentOS 7,8 or Ubuntu 18.04, 20.04.

The Role installs Python 3.8 (if is is not available on the
system already) using the follow repositories:

- CentOS 7: CentOS SCLo RH
- CentOS 8: PowerTools 
- Ubuntu 18.04: Universe

In Ubuntu 20.04 Python 3.8 is already installed. The Role also creates an
user `openquake` and generates ssh keys. Then it creates
a virtual environment for the user `openquake` in the directory
`/opt/openquake`.

Requirements
------------

**Ansible 2.9** or later. (NOTE: it might be possible to use earlier
  versions, in case of issues please try upgrading Ansible to 2.9+)

**Openssh-server** to have ssh-keygen.

This role requires root access, so either run it in a playbook with a
global `become: yes` or invoke the role in your playbook as follows:

    - hosts: server
      become: yes
      order: sorted

      roles:
        - oqengine

You can use the option `sorted` as you prefer.

Role Variables
--------------

Available variables are listed below, along with default values (see
defaults/main.yml):

- The version of the engine that is installed
    
    ```
    engine_release: "3.10.0"
    ```
    
- The requirement file for the engine 
 
     ```
    req_py38: https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt
    ```
    
- The location of the virtual environment

    ```
    venv_dir: /opt/openquake
    venv_bin: "{{ venv_dir }}/bin"
    ```
    
Dependencies
------------

None.

Example Playbook
----------------

Inventory file example for the servers section:

    [servers]
    192.168.22.21 vm_name=vm-centos-7-01
    192.168.22.22 vm_name=vm-centos-8-02
    192.168.22.23 vm_name=vm-ubuntu-1804-01
    [databases]
    192.168.22.24 vm_name=vm-ubuntu-2004-01
    [web-server]
    192.168.22.25 vm_name=vm-centos-8-03
    192.168.22.26 vm_name=vm-centos-8-04
        
Inside vars/main.yml:

    engine_release: "3.10.0"
    req_py38: https://raw.githubusercontent.com/gem/oq-engine/master/requirements-py38-linux64.txt
    venv_dir: /opt/openquake
    venv_bin: "{{ venv_dir }}/bin"
    
Use also `pre_tasks` to update the cache for Ubuntu derivatives:

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

Example of usage
----------------

To use this role you need to have ansible installed on the control
machine. Here is how to install ansible in a virtual environment:

    $ python3 -m venv venv
    $ source venv/bin/activate
    $ pip install ansible
    Successfully installed MarkupSafe-1.1.1 PyYAML-5.3.1 ansible-2.10.3 ansible-base-2.10.3 cffi-1.14.3 cryptography-3.2.1 jinja2-2.11.2 packaging-20.4 pycparser-2.20 pyparsing-2.4.7 six-1.15.0
    
 After the installation of ansible you have to define an file to use
 as inventory, for example you can define the hosts file as follow
      
    [servers]
    192.168.22.21 vm_name=vm-centos-7-01
    #
    controlmachine ansible_connection=local
 
 As you can see it is also possible to execute the playbook on localhost.
 
 To install the role you need to create a `requirements.yml` file
 and use it with ansible-galaxy
  
    # from GitHub
    # 
    - name: oqengine
      src: https://github.com/gem/oq-engine/
  
Then you can install it:
  
     $ ansible-galaxy install -r requirements.yml
 
     Starting galaxy role installation process

     - extracting oqengine to /home/users/.ansible/roles/oqengine
     - oqengine was installed successfully
 
To run the playbook on all systems listed in servers section of inventory file:
   
      ansible-playbook -i hosts  oqengine.yml
      
The oqengine.yml file is the following: 
      
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
             
If you want to run to install on localhost:
        
       $ ansible-playbook -i hosts --limit controlmachine oqengine.yml

License
-------

AGPL3
