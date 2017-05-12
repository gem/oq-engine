Classical PSHA - Loss fractions QA test
=======================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_20697.hdf5 Fri May 12 07:07:30 2017
engine_version                                   2.4.0-git7dc35c5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 12, sitecol = 1.37 KB

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
random_seed                     23                
master_seed                     0                 
avg_losses                      False             
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
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rrup rjb vs30 vs30measured z1pt0 dip mag rake ztor
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 15          2132         33,831      
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== =================================================================================
count_eff_ruptures.received    tot 16.8 KB, max_per_task 1.22 KB                                                
count_eff_ruptures.sent        sources 27.43 KB, monitor 13.7 KB, srcfilter 13.56 KB, gsims 1.34 KB, param 910 B
hazard.input_weight            3,383                                                                            
hazard.n_imts                  1 B                                                                              
hazard.n_levels                19 B                                                                             
hazard.n_realizations          1 B                                                                              
hazard.n_sites                 12 B                                                                             
hazard.n_sources               15 B                                                                             
hazard.output_weight           228                                                                              
hostname                       tstation.gem.lan                                                                 
require_epsilons               1 B                                                                              
============================== =================================================================================

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
A        1.000 0.0    1   1   4         4         
DS       2.000 NaN    2   2   1         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.083 0.289  1   2   12        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      225       AreaSource   520          0.004     1         1        
0      232       AreaSource   1,612        0.002     9         1        
0      306       AreaSource   1,768        0.0       0         0        
0      27        AreaSource   1,482        0.0       0         0        
0      137       AreaSource   2,072        0.0       0         0        
0      57        AreaSource   840          0.0       0         0        
0      8         AreaSource   4,832        0.0       0         0        
0      359       AreaSource   2,314        0.0       0         0        
0      135       AreaSource   3,285        0.0       0         0        
0      125       AreaSource   8,274        0.0       0         0        
0      101       AreaSource   559          0.0       0         0        
0      59        AreaSource   750          0.0       0         0        
0      42        AreaSource   1,755        0.0       0         0        
0      299       AreaSource   710          0.0       0         0        
0      253       AreaSource   3,058        0.0       0         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.006     15    
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.004 0.001  0.002 0.006 14       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   0.942     0.0       1     
total count_eff_ruptures         0.055     3.977     14    
managing sources                 0.015     0.0       1     
reading exposure                 0.007     0.0       1     
store source_info                8.712E-04 0.0       1     
aggregate curves                 2.615E-04 0.0       14    
saving probability maps          3.433E-05 0.0       1     
filtering composite source model 3.338E-05 0.0       1     
reading site collection          9.775E-06 0.0       1     
================================ ========= ========= ======