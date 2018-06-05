Classical Hazard QA Test, Case 25, topographic surface1 (Mt Etna)
=================================================================

============== ===================
checksum32     3,398,720,512      
date           2018-06-05T06:38:45
engine_version 3.2.0-git65c4735   
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
1         AreaSource   440          0.00458   0.00951    6.00000   20        0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.00458   1     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00468 7.900E-04 0.00278 0.00643 20       
count_eff_ruptures 0.00745 NaN       0.00745 0.00745 1        
================== ======= ========= ======= ======= =========

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
================== ====================================================================== ========
task               sent                                                                   received
RtreeFilter        srcs=24.6 KB monitor=6.76 KB srcfilter=5.45 KB                         26.53 KB
count_eff_ruptures sources=10.23 KB param=431 B monitor=353 B srcfilter=233 B gsims=130 B 359 B   
================== ====================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
PSHACalculator.run             0.45630   0.0       1     
managing sources               0.26700   0.0       1     
total prefilter                0.09353   3.46875   20    
reading composite source model 0.01385   0.0       1     
splitting sources              0.00988   0.0       1     
unpickling prefilter           0.00902   0.0       20    
total count_eff_ruptures       0.00745   5.76172   1     
store source_info              0.00713   0.0       1     
reading site collection        0.00120   0.0       1     
aggregate curves               3.378E-04 0.0       1     
unpickling count_eff_ruptures  3.228E-04 0.0       1     
saving probability maps        2.511E-04 0.0       1     
============================== ========= ========= ======