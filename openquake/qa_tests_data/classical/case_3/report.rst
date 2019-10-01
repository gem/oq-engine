Classical Hazard QA Test, Case 3
================================

============== ===================
checksum32     2,349,244,270      
date           2019-10-01T06:32:46
engine_version 3.8.0-git66affb82eb
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
0      1.00000   7,819        7,819       
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =========
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed    
========= ====== ==== ============ ========= ========= ============ =========
1         0      A    7,819        0.00134   1.00000   7,819        5,840,652
========= ====== ==== ============ ========= ========= ============ =========

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.00134   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
SourceReader       1.04072 NaN    1.04072 1.04072 1      
preclassical       0.00163 NaN    0.00163 0.00163 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
============ ======================================== ========
task         sent                                     received
SourceReader                                          6.33 KB 
preclassical srcs=3.8 KB params=518 B srcfilter=222 B 342 B   
============ ======================================== ========

Slowest operations
------------------
====================== ========= ========= ======
calc_6498              time_sec  memory_mb counts
====================== ========= ========= ======
composite source model 1.05451   0.0       1     
total SourceReader     1.04072   0.0       1     
store source_info      0.00231   0.0       1     
total preclassical     0.00163   0.0       1     
aggregate curves       2.363E-04 0.0       1     
====================== ========= ========= ======