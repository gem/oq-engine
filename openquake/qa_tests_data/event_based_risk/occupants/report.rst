event based risk
================

============== ===================
checksum32     515,431,980        
date           2019-05-10T05:07:31
engine_version 3.5.0-gitbaeb4c1e35
============== ===================

num_sites = 7, num_levels = 1, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              10000.0           
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     42                
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
occupants_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ===================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,'[BooreAtkinson2008]': [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 482          482         
================ ====== ==================== ============ ============

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 1 realization(s) x 1 loss type(s) losses x 8 bytes x 30 tasks = 1.64 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      1         S    0     2     482          0.04982   0.0       2.00000
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.04982   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ========= ========= ======= =======
operation-duration mean    stddev    min       max     outputs
read_source_models 0.00734 NaN       0.00734   0.00734 1      
sample_ruptures    0.07728 NaN       0.07728   0.07728 1      
get_eid_rlz        0.00165 3.120E-04 8.950E-04 0.00228 28     
================== ======= ========= ========= ======= =======

Data transfer
-------------
================== ============================================= ========
task               sent                                          received
read_source_models converter=305 B fnames=116 B                  1.49 KB 
sample_ruptures    param=2.81 KB sources=1.12 KB srcfilter=219 B 68.68 KB
get_eid_rlz        self=53.62 KB                                 10.71 KB
================== ============================================= ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.07728   0.0       1     
iter_ruptures            0.04912   0.0       1     
total get_eid_rlz        0.04612   0.0       28    
total read_source_models 0.00734   0.0       1     
saving ruptures          0.00491   0.0       1     
store source_info        0.00144   0.0       1     
store source model       0.00115   0.0       1     
reading exposure         6.185E-04 0.0       1     
======================== ========= ========= ======