Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     2_929_498_526      
date           2020-01-16T05:31:53
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      0.1               
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     1066              
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
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
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      1.00000   7_819        7_819       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         0      A    7_819        0.45716   1.00000   7_819       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.45716  
==== =========

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       1.14459 NaN    1.14459 1.14459 1      
preclassical       1.68542 NaN    1.68542 1.68542 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ========================================= ========
task         sent                                      received
SourceReader                                           5.74 KB 
preclassical srcs=3.82 KB params=663 B srcfilter=223 B 366 B   
============ ========================================= ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43338                  time_sec  memory_mb counts
=========================== ========= ========= ======
total preclassical          1.68542   4.98828   1     
splitting/filtering sources 1.17092   5.12891   1     
composite source model      1.15458   0.0       1     
total SourceReader          1.14459   0.0       1     
store source_info           0.00252   0.0       1     
aggregate curves            1.993E-04 0.0       1     
=========================== ========= ========= ======