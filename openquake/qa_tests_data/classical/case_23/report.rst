Classical PSHA with NZ NSHM
===========================

============== ===================
checksum32     3,211,843,635      
date           2019-09-24T15:21:27
engine_version 3.7.0-git749bb363b3
============== ===================

num_sites = 1, num_levels = 29, num_rlzs = 1

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            1.0               
complex_fault_mesh_spacing      1.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
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
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= ================ ================
smlt_path weight  gsim_logic_tree  num_realizations
========= ======= ================ ================
b1        1.00000 trivial(1,1,0,0) 1               
========= ======= ================ ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================== ========= ========== ===================
grp_id gsims                 distances siteparams ruptparams         
====== ===================== ========= ========== ===================
0      '[McVerry2006Asc]'    rrup      vs30       hypo_depth mag rake
1      '[McVerry2006SInter]' rrup      vs30       hypo_depth mag rake
====== ===================== ========= ========== ===================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================================ ====== ==================== ============ ============
source_model                     grp_id trt                  eff_ruptures tot_ruptures
================================ ====== ==================== ============ ============
NSHM_source_model-editedbkgd.xml 0      Active Shallow Crust 40           40          
NSHM_source_model-editedbkgd.xml 1      Subduction Interface 2            2           
================================ ====== ==================== ============ ============

============= ==
#TRT models   2 
#eff_ruptures 42
#tot_ruptures 42
============= ==

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
21444     1      X    1            3.734E-04 1.00000   1.00000      2,678  
21445     1      X    1            2.573E-04 1.00000   1.00000      3,887  
1         0      P    20           1.900E-04 1.00000   20           105,252
2         0      P    20           1.206E-04 1.00000   20           165,783
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
P    3.107E-04 2     
X    6.306E-04 2     
==== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ======= =======
operation-duration mean      stddev    min       max     outputs
preclassical       9.179E-04 4.063E-04 6.306E-04 0.00121 2      
read_source_models 0.16891   NaN       0.16891   0.16891 1      
================== ========= ========= ========= ======= =======

Data transfer
-------------
================== ============================================ =========
task               sent                                         received 
preclassical       srcs=809 KB params=1.42 KB srcfilter=1.26 KB 774 B    
read_source_models converter=314 B fnames=123 B                 809.06 KB
================== ============================================ =========

Slowest operations
------------------
======================== ========= ========= ======
calc_1849                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.16891   0.69922   1     
store source_info        0.00267   0.0       1     
total preclassical       0.00184   0.0       2     
aggregate curves         0.00107   0.0       2     
managing sources         4.535E-04 0.0       1     
======================== ========= ========= ======