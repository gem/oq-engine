disaggregation with a complex logic tree
========================================

============== ===================
checksum32     2,607,118,707      
date           2019-07-30T15:03:56
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 2, num_levels = 102, num_rlzs = 8

Parameters
----------
=============================== =================
calculation_mode                'preclassical'   
number_of_logic_tree_samples    0                
maximum_distance                {'default': 60.0}
investigation_time              50.0             
ses_per_logic_tree_path         1                
truncation_level                3.0              
rupture_mesh_spacing            2.0              
complex_fault_mesh_spacing      2.0              
width_of_mfd_bin                0.1              
area_source_discretization      10.0             
ground_motion_correlation_model None             
minimum_intensity               {}               
random_seed                     24               
master_seed                     0                
ses_seed                        42               
=============================== =================

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
b1        0.25000 complex(2,2)    4               
b2        0.75000 complex(2,2)    4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================= =========== ======================= =================
grp_id gsims                                     distances   siteparams              ruptparams       
====== ========================================= =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]' '[ChiouYoungs2008]'   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ========================================= =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=16, rlzs=8)>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 543          543         
source_model_1.xml 1      Stable Shallow Crust 5            4           
source_model_2.xml 2      Active Shallow Crust 543          543         
source_model_2.xml 3      Stable Shallow Crust 5            1           
================== ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 1,096
#tot_ruptures 1,091
============= =====

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ======= =======
source_id grp_id code num_ruptures calc_time num_sites weight  speed  
========= ====== ==== ============ ========= ========= ======= =======
2         1      S    4            0.00364   4.00000   5.00000 1,374  
1         0      S    543          0.00286   2.00000   543     189,871
========= ====== ==== ============ ========= ========= ======= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.00650   3     
X    0.0       1     
==== ========= ======

Duplicated sources
------------------
Found 2 unique sources and 1 duplicate sources with multiplicity 2.0: ['1']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00358 5.509E-04 0.00319 0.00397 2      
read_source_models 0.00940 0.00548   0.00552 0.01327 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================================== ========
task               sent                                                     received
preclassical       srcs=12.47 KB params=2.72 KB gsims=538 B srcfilter=440 B 694 B   
read_source_models converter=628 B fnames=206 B                             13.91 KB
================== ======================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15504               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.01880   0.0       2     
total preclassical       0.00715   0.0       2     
store source_info        0.00204   0.0       1     
managing sources         0.00137   0.0       1     
aggregate curves         2.911E-04 0.0       2     
======================== ========= ========= ======