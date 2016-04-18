Scenario QA Test 3
==================

num_sites = 4, sitecol = 877 B

Parameters
----------
============================ ================
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
concurrent_tasks             40              
avg_losses                   False           
============================ ================

Input files
-----------
======================== ====================================================
Name                     File                                                
======================== ====================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_          
job_ini                  `job.ini <job.ini>`_                                
rupture_model            `fault_rupture.xml <fault_rupture.xml>`_            
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_
======================== ====================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['ChiouYoungs2008']>

Exposure model
--------------
=========== =
#assets     4
#taxonomies 3
=========== =

======== =======
Taxonomy #Assets
======== =======
RC       1      
RM       1      
W        2      
======== =======

Slowest operations
------------------
========================= ========= ========= ======
operation                 time_sec  memory_mb counts
========================= ========= ========= ======
total scenario_risk       0.010     0.008     4     
computing individual risk 0.008     0.0       4     
filtering sites           0.006     0.0       1     
reading exposure          0.004     0.0       1     
computing gmfs            0.003     0.0       1     
saving gmfs               7.200E-04 0.0       1     
building riskinputs       5.159E-04 0.0       1     
building epsilons         4.799E-04 0.0       1     
getting hazard            1.440E-04 0.0       4     
reading site collection   6.914E-06 0.0       1     
========================= ========= ========= ======