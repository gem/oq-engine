QA test for disaggregation case_2
=================================

============== ===================
checksum32     2,473,169,806      
date           2019-09-24T15:20:59
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 2, num_levels = 1, num_rlzs = 4

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 80.0}
investigation_time              1.0              
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            4.0              
complex_fault_mesh_spacing      4.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     23               
master_seed                     0                
ses_seed                        42               
=============================== =================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ======= =============== ================
smlt_path      weight  gsim_logic_tree num_realizations
============== ======= =============== ================
source_model_1 0.50000 simple(2,1)     2               
source_model_2 0.50000 simple(2,0)     2               
============== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[YoungsEtAl1997SSlab]'                   rrup        vs30                    hypo_depth mag   
1      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=4)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Subduction Intraslab 1,815        1,815       
source_model_1.xml 1      Active Shallow Crust 3,630        3,630       
source_model_2.xml 2      Active Shallow Crust 1,420        1,420       
================== ====== ==================== ============ ============

============= =====
#TRT models   3    
#eff_ruptures 6,865
#tot_ruptures 6,865
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
2         0      A    1,815        0.00401   2.00000   3,235        806,405  
1         1      A    1,815        3.052E-04 1.00000   1,815        5,947,392
3         1      A    1,815        2.720E-04 1.00000   1,815        6,671,921
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00459   3     
S    0.0       1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ======= ========= ======= =======
operation-duration mean    stddev  min       max     outputs
preclassical       0.00177 0.00167 7.463E-04 0.00425 4      
read_source_models 0.03539 0.02512 0.01763   0.05315 2      
================== ======= ======= ========= ======= =======

Data transfer
-------------
================== ============================================ ========
task               sent                                         received
preclassical       srcs=6.96 KB srcfilter=2.8 KB params=1.97 KB 1.34 KB 
read_source_models converter=628 B fnames=210 B                 5.42 KB 
================== ============================================ ========

Slowest operations
------------------
======================== ========= ========= ======
calc_1742                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.07078   0.0       2     
total preclassical       0.00709   0.0       4     
store source_info        0.00205   0.0       1     
aggregate curves         0.00102   0.0       4     
managing sources         3.288E-04 0.0       1     
======================== ========= ========= ======