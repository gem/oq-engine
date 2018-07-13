Event Based from NonParametric source
=====================================

============== ===================
checksum32     4,272,018,576      
date           2018-06-26T14:58:20
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 3, num_levels = 7

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 500.0}
investigation_time              50.0              
ses_per_logic_tree_path         2                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.3               
area_source_discretization      20.0              
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
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1)      1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 3            4           
================ ====== ==================== ============ ============

Slowest sources
---------------
========= ========================== ============ ========= ========== ========= ========= ======
source_id source_class               num_ruptures calc_time split_time num_sites num_split events
========= ========================== ============ ========= ========== ========= ========= ======
1         NonParametricSeismicSource 1            0.01373   0.0        3.00000   3         7     
========= ========================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
========================== ========= ======
source_class               calc_time counts
========================== ========= ======
NonParametricSeismicSource 0.01373   1     
========================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
RtreeFilter        0.00504 0.00126 0.00344 0.00638 4        
compute_hazard     0.02153 NaN     0.02153 0.02153 1        
================== ======= ======= ======= ======= =========

Data transfer
-------------
============== =========================================================================================== ========
task           sent                                                                                        received
RtreeFilter    srcs=17.11 KB monitor=1.26 KB srcfilter=1.09 KB                                             14.91 KB
compute_hazard sources_or_ruptures=13.9 KB param=2.28 KB monitor=322 B rlzs_by_gsim=297 B src_filter=246 B 27.08 KB
============== =========================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.06748   0.0       1     
managing sources               0.04770   0.0       1     
total compute_hazard           0.02153   7.82031   1     
total prefilter                0.02015   3.56641   4     
building ruptures              0.01840   6.91016   1     
making contexts                0.01274   0.0       3     
saving ruptures                0.00740   0.0       1     
store source_info              0.00534   0.0       1     
unpickling prefilter           0.00113   0.0       4     
unpickling compute_hazard      8.237E-04 0.0       1     
GmfGetter.init                 3.843E-04 0.0       1     
reading site collection        3.395E-04 0.0       1     
splitting sources              3.135E-04 0.0       1     
aggregating hcurves            2.031E-04 0.0       1     
============================== ========= ========= ======