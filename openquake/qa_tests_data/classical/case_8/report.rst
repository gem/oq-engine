Classical Hazard QA Test, Case 8
================================

============== ===================
checksum32     3_078_626_546      
date           2020-01-16T05:31:15
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                0.0               
rupture_mesh_spacing            0.1               
complex_fault_mesh_spacing      0.1               
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
b1_b2     0.30000 trivial(1)      1               
b1_b3     0.30000 trivial(1)      1               
b1_b4     0.40000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      3.333E-04 3_000        3_000       
1      3.333E-04 3_000        3_000       
2      3.333E-04 3_000        3_000       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
1         1      P    3_000        0.01193   3.333E-04 3_000       
1         0      P    3_000        0.01178   3.333E-04 3_000       
1         2      P    3_000        0.00681   3.333E-04 3_000       
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
P    0.03053  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.03174 0.01602 0.02221 0.05023 3      
preclassical       0.01125 0.00317 0.00759 0.01318 3      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=3.79 KB ltmodel=576 B fname=309 B 77.03 KB
preclassical srcs=3.48 KB params=1.97 KB srcfilter=669 B 1.08 KB 
============ =========================================== ========

Slowest operations
------------------
=========================== ========= ========= ======
calc_43313                  time_sec  memory_mb counts
=========================== ========= ========= ======
total SourceReader          0.09522   0.84375   3     
composite source model      0.07236   0.48047   1     
total preclassical          0.03376   0.0       3     
store source_info           0.00271   0.0       1     
splitting/filtering sources 9.089E-04 0.0       3     
aggregate curves            7.520E-04 0.0       3     
=========================== ========= ========= ======