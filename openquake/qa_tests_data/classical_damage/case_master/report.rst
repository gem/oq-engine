classical damage hazard
=======================

============== ===================
checksum32     3,129,914,875      
date           2019-06-24T15:33:42
engine_version 3.6.0-git4b6205639c
============== ===================

num_sites = 7, num_levels = 79, num_rlzs = 8

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
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
=============================== ==================

Input files
-----------
======================= ========================================================================
Name                    File                                                                    
======================= ========================================================================
contents_fragility      `contents_fragility_model.xml <contents_fragility_model.xml>`_          
exposure                `exposure_model.xml <exposure_model.xml>`_                              
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                            
job_ini                 `job_haz.ini <job_haz.ini>`_                                            
nonstructural_fragility `nonstructural_fragility_model.xml <nonstructural_fragility_model.xml>`_
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_fragility    `structural_fragility_model.xml <structural_fragility_model.xml>`_      
======================= ========================================================================

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
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= ===
#TRT models   4  
#eff_ruptures 969
#tot_ruptures 969
#tot_weight   969
============= ===

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight  checksum     
====== ========= ==== ===== ===== ============ ========= ========= ======= =============
0      1         S    0     2     482          0.00611   7.00000   669     2,786,737,502
1      2         S    2     4     4            0.00353   7.00000   5.55673 3,056,286,023
3      2         X    6     402   1            0.00254   7.00000   1.38918 2,506,021,815
2      1         S    4     6     482          0.0       0.0       0.0     2,786,737,502
====== ========= ==== ===== ===== ============ ========= ========= ======= =============

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.00964   3     
X    0.00254   1     
==== ========= ======

Duplicated sources
------------------
Found 2 source(s) with the same ID and 1 true duplicate(s): ['1']
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.00666 1.146E-05 0.00665 0.00667 2      
read_source_models 0.01235 0.00289   0.01030 0.01439 2      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================== ======================================================== ========
task               sent                                                     received
preclassical       srcs=12.48 KB params=2.42 KB gsims=538 B srcfilter=440 B 744 B   
read_source_models converter=626 B fnames=240 B                             13.95 KB
================== ======================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.02469   0.0       2     
total preclassical       0.01332   0.0       2     
managing sources         0.00362   0.0       1     
store source_info        0.00192   0.0       1     
reading exposure         6.502E-04 0.0       1     
aggregate curves         4.077E-04 0.0       2     
======================== ========= ========= ======