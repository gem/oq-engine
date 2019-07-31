Classical PSHA that utilises Christchurch-specific gsims and GMtoLHC horizontal component conversion
====================================================================================================

============== ===================
checksum32     3,681,125,057      
date           2019-07-30T15:04:20
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 2, num_levels = 4, num_rlzs = 2

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.1               
area_source_discretization      None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     20                
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
site_model              `site_model.xml <site_model.xml>`_                          
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
smb1      1.00000 simple(2)       2               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ====================================================== =========== ========================================= ============================
grp_id gsims                                                  distances   siteparams                                ruptparams                  
====== ====================================================== =========== ========================================= ============================
0      '[Bradley2013bChchMaps]' '[McVerry2006ChchStressDrop]' rjb rrup rx lat lon siteclass vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ====================================================== =========== ========================================= ============================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=2)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ======= =====
source_id grp_id code num_ruptures calc_time num_sites weight  speed
========= ====== ==== ============ ========= ========= ======= =====
1         0      X    1            0.00134   2.00000   1.00000 744  
========= ====== ==== ============ ========= ========= ======= =====

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00134   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00163 NaN    0.00163 0.00163 1      
read_source_models 0.02468 NaN    0.02468 0.02468 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ===================================================== ========
task               sent                                                  received
preclassical       srcs=2.95 KB params=525 B gsims=292 B srcfilter=220 B 342 B   
read_source_models converter=306 B fnames=100 B                          3.36 KB 
================== ===================================================== ========

Slowest operations
------------------
======================== ======== ========= ======
calc_15526               time_sec memory_mb counts
======================== ======== ========= ======
total read_source_models 0.02468  0.0       1     
store source_info        0.00717  0.0       1     
total preclassical       0.00163  0.0       1     
managing sources         0.00146  0.0       1     
aggregate curves         0.00115  0.0       1     
======================== ======== ========= ======