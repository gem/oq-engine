Classical PSHA with site class as a site variable
=================================================

============== ===================
checksum32     3,190,932,410      
date           2019-07-30T15:04:33
engine_version 3.7.0-git3b3dff46da
============== ===================

num_sites = 1, num_levels = 14, num_rlzs = 1

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
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
smb1      1.00000 trivial(1)      1               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ========= ========== ===================
grp_id gsims                distances siteparams ruptparams         
====== ==================== ========= ========== ===================
0      '[McVerry2006AscSC]' rrup      siteclass  hypo_depth mag rake
====== ==================== ========= ========== ===================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 310          310         
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ====== =======
source_id grp_id code num_ruptures calc_time num_sites weight speed  
========= ====== ==== ============ ========= ========= ====== =======
2         0      S    310          0.00284   1.00000   310    109,034
========= ====== ==== ============ ========= ========= ====== =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.00284   1     
==== ========= ======

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
preclassical       0.00314 NaN    0.00314 0.00314 1      
read_source_models 0.00440 NaN    0.00440 0.00440 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ===================================================== ========
task               sent                                                  received
preclassical       srcs=1.15 KB params=607 B srcfilter=220 B gsims=152 B 342 B   
read_source_models converter=306 B fnames=100 B                          1.55 KB 
================== ===================================================== ========

Slowest operations
------------------
======================== ========= ========= ======
calc_15547               time_sec  memory_mb counts
======================== ========= ========= ======
total read_source_models 0.00440   0.0       1     
total preclassical       0.00314   0.0       1     
store source_info        0.00202   0.0       1     
managing sources         9.770E-04 0.0       1     
aggregate curves         1.380E-04 0.0       1     
======================== ========= ========= ======