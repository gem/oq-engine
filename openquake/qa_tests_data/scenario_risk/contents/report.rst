QA Scenario Risk for contents
=============================

Datastore /home/michele/ssd/calc_11459.hdf5 last updated Wed Apr 20 09:39:27 2016 on gem-tstation

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'scenario_risk'    
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 300}   
investigation_time           None               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         10.0               
complex_fault_mesh_spacing   10.0               
width_of_mfd_bin             None               
area_source_discretization   None               
random_seed                  3                  
master_seed                  0                  
avg_losses                   False              
oqlite_version               '0.13.0-git361357f'
============================ ===================

Input files
-----------
======================== ========================================================================
Name                     File                                                                    
======================== ========================================================================
contents_vulnerability   `vulnerability_model_contents.xml <vulnerability_model_contents.xml>`_  
exposure                 `exposure_model.xml <exposure_model.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                    
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_                                
structural_vulnerability `vulnerability_model_structure.xml <vulnerability_model_structure.xml>`_
======================== ========================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     3
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
RC       1      
RM       1      
W        1      
======== =======

Slowest operations
------------------
========================= ========= ========= ======
operation                 time_sec  memory_mb counts
========================= ========= ========= ======
total scenario_risk       0.007     0.004     3     
computing individual risk 0.006     0.0       3     
filtering sites           0.006     0.0       1     
reading exposure          0.003     0.0       1     
computing gmfs            9.608E-04 0.0       1     
saving gmfs               6.568E-04 0.0       1     
building riskinputs       2.718E-04 0.0       1     
building epsilons         9.799E-05 0.0       1     
getting hazard            8.416E-05 0.0       3     
reading site collection   7.153E-06 0.0       1     
========================= ========= ========= ======