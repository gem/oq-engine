Classical PSHA that utilises Christchurch-specific gsims and GMtoLHC horizontal component conversion
====================================================================================================

============== ===================
checksum32     3,681,125,057      
date           2019-05-10T05:07:51
engine_version 3.5.0-gitbaeb4c1e35
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

  <RlzsAssoc(size=2, rlzs=2)
  0,'[Bradley2013bChchMaps]': [0]
  0,'[McVerry2006ChchStressDrop]': [1]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
================ ====== ==================== ============ ============

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time num_sites weight 
====== ========= ==== ===== ===== ============ ========= ========= =======
0      1         X    0     57    1            0.00299   2.00000   1.41421
====== ========= ==== ===== ===== ============ ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
X    0.00299   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.02009 NaN    0.02009 0.02009 1      
preclassical       0.00348 NaN    0.00348 0.00348 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ===================================================== ========
task               sent                                                  received
read_source_models converter=305 B fnames=107 B                          3.36 KB 
preclassical       srcs=2.93 KB params=486 B gsims=292 B srcfilter=219 B 343 B   
================== ===================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.02009   0.0       1     
total preclassical       0.00348   0.0       1     
managing sources         0.00327   0.0       1     
store source_info        0.00175   0.0       1     
aggregate curves         1.488E-04 0.0       1     
======================== ========= ========= ======