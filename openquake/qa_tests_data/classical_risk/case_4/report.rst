Classical Hazard-Risk QA test 4
===============================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21268.hdf5 Fri May 12 10:45:14 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 6, sitecol = 1.05 KB

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
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
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): ['<0,b1~b1,w=0.4>']
  0,ChiouYoungs2008(): ['<1,b1~b2,w=0.6>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 39          6405         91,021      
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================== ====================================================================================
count_eff_ruptures.received    tot 23.56 KB, max_per_task 1.2 KB                                                   
count_eff_ruptures.sent        sources 53.11 KB, monitor 19.18 KB, srcfilter 16.09 KB, gsims 3.42 KB, param 1.27 KB
hazard.input_weight            9,102                                                                               
hazard.n_imts                  1 B                                                                                 
hazard.n_levels                19 B                                                                                
hazard.n_realizations          2 B                                                                                 
hazard.n_sites                 6 B                                                                                 
hazard.n_sources               39 B                                                                                
hazard.output_weight           114                                                                                 
hostname                       tstation.gem.lan                                                                    
require_epsilons               1 B                                                                                 
============================== ====================================================================================

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   6         6         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      231       AreaSource   4,185        0.002     6         1        
0      376       AreaSource   2,220        8.209E-04 1         1        
0      127       AreaSource   2,940        0.0       0         0        
0      270       AreaSource   7,837        0.0       0         0        
0      89        AreaSource   810          0.0       0         0        
0      288       AreaSource   2,430        0.0       0         0        
0      42        AreaSource   1,755        0.0       0         0        
0      137       AreaSource   2,072        0.0       0         0        
0      10        AreaSource   1,920        0.0       0         0        
0      28        AreaSource   2,548        0.0       0         0        
0      343       AreaSource   2,926        0.0       0         0        
0      27        AreaSource   1,482        0.0       0         0        
0      298       AreaSource   2,744        0.0       0         0        
0      177       AreaSource   846          0.0       0         0        
0      369       AreaSource   826          0.0       0         0        
0      257       AreaSource   2,850        0.0       0         0        
0      291       AreaSource   2,350        0.0       0         0        
0      161       AreaSource   552          0.0       0         0        
0      395       AreaSource   2,720        0.0       0         0        
0      132       AreaSource   4,131        0.0       0         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.003     39    
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.004 0.001  0.002 0.007 20       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   2.126     0.0       1     
total count_eff_ruptures         0.077     0.012     20    
managing sources                 0.022     0.0       1     
reading exposure                 0.007     0.0       1     
store source_info                8.166E-04 0.0       1     
aggregate curves                 2.797E-04 0.0       20    
filtering composite source model 5.913E-05 0.0       1     
saving probability maps          2.861E-05 0.0       1     
reading site collection          8.106E-06 0.0       1     
================================ ========= ========= ======