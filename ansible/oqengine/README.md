Ansible Role: oqengine
=========

Installs oq-engine from pypip on CentOS 7,8 or Ubuntu 1804, 2004. 
The Role first of all check if on the system there is installed python and if the version the installed version is not the 3.8 it setup the python virtual environment on the system using python3.8 that is installed using the follow repository:
CentOS 7: CentOS SCLo RH
CentOS 8: PowerTools 
Ubuntu 1804: Universe
Ubuntu 2004: python3.8 is the default version 


Requirements
------------

Ansible 2.9 or later. (NOTE: it might be possible to use earlier versions, in case of issues please try updating Ansible to 2.9+)
note that this role requires root access, so either run it in a playbook with a global become: yes, or invoke the role in your playbook like:

    - hosts: server
      become: yes
      order: sorted

      roles:
         - oqengine

You can use the option sorted as you prefer

Role Variables
--------------



Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:


Use also pre_tasks to assure to update the cache for Debian derivate

      pre_tasks:
        - name: Update apt cache.
          apt:
            update_cache: true
            cache_valid_time: 600
          when: ansible_os_family == 'Debian'


License
-------

AGPL3

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
