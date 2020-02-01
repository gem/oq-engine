Classical Hazard QA Test, Case 9
================================

============== ===================
checksum32     3_616_596_807      
date           2020-01-16T05:31:17
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.01              
complex_fault_mesh_spacing      0.01              
width_of_mfd_bin                0.001             
area_source_discretization      10.0              
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
b1_b2     0.50000 trivial(1)      1               
b1_b3     0.50000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.333E-04 3_000        3_000       
1      2.857E-04 3_500        3_500       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      P    3_500        0.01049   2.857E-04 3_500       
1         0      P    3_000        0.00953   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.02003  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.02235 0.00107   0.02160 0.02311 2      
preclassical       0.01107 6.607E-04 0.01060 0.01153 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=2.36 KB ltmodel=384 B fname=206 B 55.25 KB
preclassical srcs=2.32 KB params=1.31 KB srcfilter=446 B 734 B   
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43319                  time_sec  memory_mb counts
=========================== ========= ========= ======
total SourceReader          0.04470   0.25000   2     
composite source model      0.04401   0.0       1     
total preclassical          0.02213   0.0       2     
store source_info           0.00225   0.0       1     
splitting/filtering sources 7.446E-04 0.0       2     
aggregate curves            6.003E-04 0.0       2     
=========================== ========= ========= ======