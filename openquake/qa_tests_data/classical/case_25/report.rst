Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

============== ===================
checksum32     3,398,720,512      
date           2018-09-05T10:04:31
engine_version 3.2.0-gitb4ef3a4b6c
============== ===================

num_sites = 6, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      1.0               
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
sites                   `sites.csv <sites.csv>`_                                    
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========== ========== ==========
grp_id gsims                 distances  siteparams ruptparams
====== ===================== ========== ========== ==========
0      TusaLanger2016Rhypo() rhypo rrup vs30       mag       
====== ===================== ========== ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,TusaLanger2016Rhypo(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======== ============ ============
source_model     grp_id trt      eff_ruptures tot_ruptures
================ ====== ======== ============ ============
source_model.xml 0      Volcanic 440          440         
================ ====== ======== ============ ============

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
1         AreaSource   440          0.00543   0.00750    6.00000   20        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00543   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
==================== ======= ========= ======= ======= =========
operation-duration   mean    stddev    min     max     num_tasks
pickle_source_models 0.00859 NaN       0.00859 0.00859 1        
count_eff_ruptures   0.00636 NaN       0.00636 0.00636 1        
preprocess           0.00277 7.305E-04 0.00164 0.00418 10       
==================== ======= ========= ======= ======= =========

Fastest task
------------
taskno=1, weight=107, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   6.00000 0.0    6       6       20
weight   5.38888 0.0    5.38888 5.38888 20
======== ======= ====== ======= ======= ==

Slowest task
------------
taskno=1, weight=107, duration=0 s, sources="1"

======== ======= ====== ======= ======= ==
variable mean    stddev min     max     n 
======== ======= ====== ======= ======= ==
nsites   6.00000 0.0    6       6       20
weight   5.38888 0.0    5.38888 5.38888 20
======== ======= ====== ======= ======= ==

Data transfer
-------------
==================== ===================================================================== ========
task                 sent                                                                  received
pickle_source_models monitor=0 B fnames=0 B converter=0 B                                  156 B   
count_eff_ruptures   sources=8.15 KB param=506 B monitor=307 B srcfilter=220 B gsims=130 B 359 B   
preprocess           srcs=14.19 KB monitor=3.12 KB srcfilter=2.47 KB param=360 B           15.47 KB
==================== ===================================================================== ========

Slowest operations
------------------
========================== ========= ========= ======
operation                  time_sec  memory_mb counts
========================== ========= ========= ======
managing sources           0.05114   0.0       1     
total preprocess           0.02772   2.39062   10    
total pickle_source_models 0.00859   0.0       1     
splitting sources          0.00777   0.0       1     
total count_eff_ruptures   0.00636   4.65234   1     
store source_info          0.00498   0.0       1     
aggregate curves           2.198E-04 0.0       1     
========================== ========= ========= ======