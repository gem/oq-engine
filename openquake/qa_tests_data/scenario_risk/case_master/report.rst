scenario risk
=============

============================================ ========================
gem-tstation:/mnt/ssd/oqdata/calc_85599.hdf5 Tue Feb 14 15:49:00 2017
engine_version                               2.3.0-git1f56df2        
hazardlib_version                            0.23.0-git6937706       
============================================ ========================

num_sites = 7, sitecol = 1.11 KB

Parameters
----------
=============================== ==================
calculation_mode                'scenario_risk'   
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
random_seed                     42                
master_seed                     42                
avg_losses                      False             
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
rupture_model                       `rupture_model.xml <rupture_model.xml>`_                                        
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008(): ['<0,b_1~b1,w=0.75>']
  0,ChiouYoungs2008(): ['<1,b_1~b2,w=0.25>']>

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
tax1     1.000 0.0    1   1   4         4         
tax2     1.000 0.0    1   1   2         2         
tax3     1.000 NaN    1   1   1         1         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest operations
------------------
======================= ========= ========= ======
operation               time_sec  memory_mb counts
======================= ========= ========= ======
computing gmfs          0.021     0.0       1     
filtering sites         0.010     0.0       1     
reading exposure        0.005     0.0       1     
saving gmfs             0.003     0.0       1     
building riskinputs     7.973E-04 0.0       1     
building epsilons       2.196E-04 0.0       1     
reading site collection 7.391E-06 0.0       1     
======================= ========= ========= ======