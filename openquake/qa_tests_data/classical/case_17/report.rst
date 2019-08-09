Classical Hazard QA Test, Case 17
=================================

============== ===================
checksum32     1,496,028,179      
date           2019-07-30T15:04:28
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 3, num_rlzs = 5

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    5                 
maximum_distance                {'default': 200.0}
investigation_time              1000.0            
ses_per_logic_tree_path         1                 
truncation_level                2.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
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
b1        0.20000 trivial(1)      1               
b2        0.20000 trivial(1)      1               
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

  <RlzsAssoc(size=2, rlzs=5)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 46           39          
source_model_2.xml 1      Active Shallow Crust 46           7           
================== ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 92
#tot_ruptures 46
============= ==

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== ======
source_id grp_id code num_ruptures calc_time num_sites weight speed 
========= ====== ==== ============ ========= ========= ====== ======
1         0      P    39           0.00129   2.00000   46     35,525
========= ====== ==== ============ ========= ========= ====== ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    0.00129   2     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
preclassical       0.00162   NaN       0.00162   0.00162 1      
read_source_models 9.358E-04 3.176E-04 7.112E-04 0.00116 2      
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ==================================================== ========
task               sent                                                 received
preclassical       srcs=1.8 KB params=517 B srcfilter=220 B gsims=147 B 347 B   
read_source_models converter=628 B fnames=204 B                         3.39 KB 
================== ==================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15531               time_sec  memory_mb counts
======================== ========= ========= ======
store source_info        0.00209   0.0       1     
total read_source_models 0.00187   0.0       2     
total preclassical       0.00162   0.0       1     
managing sources         9.570E-04 0.0       1     
aggregate curves         1.450E-04 0.0       1     
======================== ========= ========= ======