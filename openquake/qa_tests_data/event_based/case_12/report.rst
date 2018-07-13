Event Based QA Test, Case 12
============================

============== ===================
checksum32     459,911,748        
date           2018-06-26T14:58:36
engine_version 3.2.0-gitb0cd949   
============== ===================

num_sites = 1, num_levels = 3

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         3500              
truncation_level                2.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     42                
master_seed                     0                 
ses_seed                        1066              
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        1.00000 trivial(1,1)    1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================== ========= ========== ==========
grp_id gsims               distances siteparams ruptparams
====== =================== ========= ========== ==========
0      SadighEtAl1997()    rrup      vs30       mag rake  
1      BooreAtkinson2008() rjb       vs30       mag rake  
====== =================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,SadighEtAl1997(): [0]
  1,BooreAtkinson2008(): [0]>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== ============ ============
source_model     grp_id trt                  eff_ruptures tot_ruptures
================ ====== ==================== ============ ============
source_model.xml 0      Active Shallow Crust 1            1           
source_model.xml 1      Stable Continental   1            1           
================ ====== ==================== ============ ============

============= =
#TRT models   2
#eff_ruptures 2
#tot_ruptures 2
#tot_weight   2
============= =

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
2         PointSource  1            0.02457   0.0        1.00000   1         3,370 
1         PointSource  1            0.02341   0.0        1.00000   1         3,536 
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.04798   2     
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =========
operation-duration mean    stddev    min     max     num_tasks
RtreeFilter        0.00152 5.665E-05 0.00148 0.00156 2        
compute_hazard     0.10463 9.124E-04 0.10399 0.10528 2        
================== ======= ========= ======= ======= =========

Data transfer
-------------
============== =========================================================================================== =========
task           sent                                                                                        received 
RtreeFilter    srcs=2.55 KB monitor=644 B srcfilter=558 B                                                  2.64 KB  
compute_hazard param=4.79 KB sources_or_ruptures=2.72 KB monitor=644 B rlzs_by_gsim=591 B src_filter=492 B 301.79 KB
============== =========================================================================================== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.22552   0.0       1     
total compute_hazard           0.20927   8.58203   2     
building hazard                0.13307   0.53125   2     
saving ruptures                0.06857   0.0       2     
building ruptures              0.05982   7.32422   2     
store source_info              0.00695   0.0       1     
saving gmfs                    0.00586   0.0       2     
total prefilter                0.00304   1.19531   2     
reading composite source model 0.00279   0.0       1     
GmfGetter.init                 0.00198   0.0       2     
saving gmf_data/indices        0.00194   0.0       1     
making contexts                0.00156   0.0       2     
unpickling compute_hazard      0.00151   0.0       2     
aggregating hcurves            6.981E-04 0.0       2     
unpickling prefilter           5.538E-04 0.0       2     
building hazard curves         4.966E-04 0.0       2     
reading site collection        3.560E-04 0.0       1     
splitting sources              2.937E-04 0.0       1     
============================== ========= ========= ======