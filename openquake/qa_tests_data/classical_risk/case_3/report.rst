Classical PSHA - Loss fractions QA test
=======================================

============== ===================
checksum32     177,006,542        
date           2018-04-19T05:01:41
engine_version 3.1.0-git9c5da5b   
============== ===================

num_sites = 12, num_levels = 19

Parameters
----------
=============================== ==================
calculation_mode                'classical_risk'  
number_of_logic_tree_samples    1                 
maximum_distance                {'default': 200.0}
investigation_time              50.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      5.0               
width_of_mfd_bin                0.2               
area_source_discretization      10.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     23                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== =============== ================
smlt_path weight gsim_logic_tree num_realizations
========= ====== =============== ================
b1        1.000  trivial(1)      1/1             
========= ====== =============== ================

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
source_model.xml 0      Active Shallow Crust 1,638        33,831      
================ ====== ==================== ============ ============

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
W        1.000 0.0    1   1   5         5         
A        1.000 0.0    1   1   4         4         
DS       2.000 NaN    2   2   1         2         
UFB      1.000 0.0    1   1   2         2         
*ALL*    1.083 0.289  1   2   12        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
========= ============ ============ ========= ========== ========= ========= ======
source_id source_class num_ruptures calc_time split_time num_sites num_split events
========= ============ ============ ========= ========== ========= ========= ======
232       AreaSource   1,612        0.035     0.056      586       124       0     
225       AreaSource   520          3.855E-04 0.018      2         2         0     
57        AreaSource   840          0.0       0.025      0         0         0     
299       AreaSource   710          0.0       0.027      0         0         0     
125       AreaSource   8,274        0.0       0.384      0         0         0     
359       AreaSource   2,314        0.0       0.092      0         0         0     
27        AreaSource   1,482        0.0       0.058      0         0         0     
8         AreaSource   4,832        0.0       1.006      0         0         0     
59        AreaSource   750          0.0       0.026      0         0         0     
42        AreaSource   1,755        0.0       0.055      0         0         0     
135       AreaSource   3,285        0.0       0.186      0         0         0     
137       AreaSource   2,072        0.0       0.111      0         0         0     
101       AreaSource   559          0.0       0.029      0         0         0     
253       AreaSource   3,058        0.0       0.119      0         0         0     
306       AreaSource   1,768        0.0       0.093      0         0         0     
========= ============ ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.036     15    
============ ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.023 0.022  0.007 0.039 2        
================== ===== ====== ===== ===== =========

Informational data
------------------
============== ========================================================================== ========
task           sent                                                                       received
count_ruptures sources=30.27 KB srcfilter=2.58 KB param=1.07 KB monitor=660 B gsims=254 B 803 B   
============== ========================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
splitting sources              2.290     1.461     1     
reading composite source model 2.047     0.0       1     
managing sources               0.460     0.0       1     
total count_ruptures           0.046     2.516     2     
reading exposure               0.021     0.0       1     
store source_info              0.006     0.0       1     
reading site collection        0.006     0.0       1     
unpickling count_ruptures      1.063E-04 0.0       2     
aggregate curves               5.436E-05 0.0       2     
saving probability maps        3.910E-05 0.0       1     
============================== ========= ========= ======