Calculation of the ground motion fields for a scenario
======================================================

============== ===================
checksum32     4,182,813,640      
date           2019-05-10T05:07:24
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 7, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'scenario'        
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              None              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                None              
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     3                 
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
============= ==========================================
Name          File                                      
============= ==========================================
exposure      `exposure_model.xml <exposure_model.xml>`_
job_ini       `job_haz.ini <job_haz.ini>`_              
rupture_model `fault_rupture.xml <fault_rupture.xml>`_  
============= ==========================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b_1       1.00000 trivial(1)      1               
========= ======= =============== ================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[ChiouYoungs2008]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
============ ====== === ============ ============
source_model grp_id trt eff_ruptures tot_ruptures
============ ====== === ============ ============
scenario     0      *   1            0           
============ ====== === ============ ============

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     4       
deductibile     relative
insurance_limit relative
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
W        1.00000 NaN    1   1   1         1         
A        1.00000 0.0    1   1   4         4         
DS       1.00000 NaN    1   1   1         1         
UFB      1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest operations
------------------
================ ======== ========= ======
operation        time_sec memory_mb counts
================ ======== ========= ======
reading exposure 0.00186  0.0       1     
================ ======== ========= ======