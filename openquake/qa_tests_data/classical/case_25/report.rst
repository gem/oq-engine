Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

============== ===================
checksum32     3,398,720,512      
date           2018-04-30T11:21:48
engine_version 3.1.0-gitb0812f0   
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
====== ===================== ========= ========== ==========
grp_id gsims                 distances siteparams ruptparams
====== ===================== ========= ========== ==========
0      TusaLanger2016Rhypo() rhypo     vs30       mag       
====== ===================== ========= ========== ==========

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
1         AreaSource   440          2.062E-04 0.00899    120       20        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   2.062E-04 1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =========
operation-duration mean    stddev min     max     num_tasks
count_ruptures     0.00299 NaN    0.00299 0.00299 1        
================== ======= ====== ======= ======= =========

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

Informational data
------------------
============== ==================================================================== ========
task           sent                                                                 received
count_ruptures sources=6.3 KB srcfilter=989 B param=412 B monitor=330 B gsims=130 B 359 B   
============== ==================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.01321   0.0       1     
splitting sources              0.00948   0.0       1     
managing sources               0.00575   0.0       1     
store source_info              0.00360   0.0       1     
total count_ruptures           0.00299   1.07422   1     
reading site collection        5.739E-04 0.0       1     
unpickling count_ruptures      4.292E-05 0.0       1     
saving probability maps        3.314E-05 0.0       1     
aggregate curves               2.241E-05 0.0       1     
============================== ========= ========= ======