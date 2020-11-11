Classical PSHA Risk QA Test Case 1
==================================

num_sites = 1

Parameters
----------
============================ ==============
calculation_mode             classical_risk
number_of_logic_tree_samples 0             
maximum_distance             None          
investigation_time           None          
ses_per_logic_tree_path      1             
truncation_level             None          
rupture_mesh_spacing         None          
complex_fault_mesh_spacing   None          
width_of_mfd_bin             None          
area_source_discretization   None          
random_seed                  42            
master_seed                  0             
concurrent_tasks             32            
avg_losses                   False         
============================ ==============

Input files
-----------
======================== ================================================
Name                     File                                            
======================== ================================================
exposure                 `exposure.xml <exposure.xml>`_                  
hazard_curves            `hazard_curve-mean.xml <hazard_curve-mean.xml>`_
job_ini                  `job_risk.ini <job_risk.ini>`_                  
structural_vulnerability `vulnerability.xml <vulnerability.xml>`_        
======================== ================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,FromFile: ['FromFile']>

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== =======
Taxonomy #Assets
======== =======
VF       1      
======== =======