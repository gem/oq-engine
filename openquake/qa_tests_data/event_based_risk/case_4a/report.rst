Event Based Hazard
==================

gem-tstation:/home/michele/ssd/calc_22579.hdf5 updated Tue May 31 15:37:09 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===============================
calculation_mode             'event_based'                  
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           1.0                            
ses_per_logic_tree_path      100                            
truncation_level             3.0                            
rupture_mesh_spacing         2.0                            
complex_fault_mesh_spacing   2.0                            
width_of_mfd_bin             0.1                            
area_source_discretization   10.0                           
random_seed                  24                             
master_seed                  0                              
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_hazard.ini <job_hazard.ini>`_                                        
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `source_model.xml <source_model.xml>`_                                    
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           5            483   
================ ====== ==================== =========== ============ ======

Informational data
------------------
================ ============
hostname         gem-tstation
require_epsilons 1           
================ ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 5    
Total number of events   6    
Rupture multiplicity     1.200
======================== =====

Exposure model
--------------
=========== =
#assets     1
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Wood     1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ========================= ====== ========= =========== ========== =========
src_group_id source_id source_class              weight split_num filter_time split_time calc_time
============ ========= ========================= ====== ========= =========== ========== =========
0            3         SimpleFaultSource         482    15        0.002       0.029      0.225    
0            1         CharacteristicFaultSource 1.000  1         0.001       0.0        0.022    
============ ========= ========================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
========================= =========== ========== ========= ======
source_class              filter_time split_time calc_time counts
========================= =========== ========== ========= ======
CharacteristicFaultSource 0.001       0.0        0.022     1     
SimpleFaultSource         0.002       0.029      0.225     1     
========================= =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.017 0.008  0.008 0.037 15       
compute_ruptures.memory_mb        0.0   0.0    0.0   0.0   15       
compute_gmfs_and_curves.time_sec  0.008 0.007  0.004 0.021 5        
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   5        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         0.253     0.0       15    
managing sources               0.047     0.0       1     
total compute_gmfs_and_curves  0.039     0.0       5     
filtering ruptures             0.030     0.0       5     
make contexts                  0.030     0.0       5     
splitting sources              0.029     0.0       1     
reading composite source model 0.012     0.0       1     
compute poes                   0.007     0.0       5     
store source_info              0.006     0.0       1     
saving ruptures                0.004     0.0       1     
reading exposure               0.003     0.0       1     
filtering sources              0.003     0.0       2     
aggregate curves               0.003     0.0       15    
saving gmfs                    0.002     0.0       5     
reading site collection        6.914E-06 0.0       1     
============================== ========= ========= ======