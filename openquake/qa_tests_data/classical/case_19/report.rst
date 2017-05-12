SHARE OpenQuake Computational Settings
======================================

================================================ ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_21341.hdf5 Fri May 12 10:46:01 2017
engine_version                                   2.4.0-git59713b5        
hazardlib_version                                0.24.0-git0596dd3       
================================================ ========================

num_sites = 1, sitecol = 809 B

Parameters
----------
=============================== ===========================================
calculation_mode                'classical'                                
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (8, 200)]}
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
=============================== ===========================================

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ====== ============================================================== ====================== ================
smlt_path weight source_model_file                                              gsim_logic_tree        num_realizations
========= ====== ============================================================== ====================== ================
b1        1.000  `simple_area_source_model.xml <simple_area_source_model.xml>`_ complex(0,4,5,2,0,1,4) 4/4             
========= ====== ============================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ========== ==============
grp_id gsims                                                                                distances  siteparams ruptparams    
====== ==================================================================================== ========== ========== ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rrup vs30       hypo_depth mag
====== ==================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  4,AtkinsonBoore2003SSlab(): ['<0,b1~@_@_@_@_b51_@_@,w=0.2>']
  4,LinLee2008SSlab(): ['<1,b1~@_@_@_@_b52_@_@,w=0.2>']
  4,YoungsEtAl1997SSlab(): ['<2,b1~@_@_@_@_b53_@_@,w=0.2>']
  4,ZhaoEtAl2006SSlab(): ['<3,b1~@_@_@_@_b54_@_@,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= =========== ============ ============
source_model                 grp_id trt               num_sources eff_ruptures tot_ruptures
============================ ====== ================= =========== ============ ============
simple_area_source_model.xml 4      Subduction Inslab 7           7770         93,219      
============================ ====== ================= =========== ============ ============

Informational data
------------------
============================== ================================================================================
count_eff_ruptures.received    tot 16.76 KB, max_per_task 1.88 KB                                              
count_eff_ruptures.sent        sources 48.65 KB, monitor 14.79 KB, srcfilter 6.8 KB, gsims 2.47 KB, param 585 B
hazard.input_weight            197,635                                                                         
hazard.n_imts                  3 B                                                                             
hazard.n_levels                78 B                                                                            
hazard.n_realizations          1.25 KB                                                                         
hazard.n_sites                 1 B                                                                             
hazard.n_sources               18 B                                                                            
hazard.output_weight           78                                                                              
hostname                       tstation.gem.lan                                                                
require_epsilons               0 B                                                                             
============================== ================================================================================

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
4      s46       AreaSource         7,770        0.002     1         1        
4      s40       AreaSource         12,327       0.0       0         0        
3      scr293    AreaSource         61,740       0.0       0         0        
2      sh13      AreaSource         41,952       0.0       0         0        
1      v4        AreaSource         168          0.0       0         0        
1      v1        AreaSource         42           0.0       0         0        
3      scr304    AreaSource         574          0.0       0         0        
0      i20       ComplexFaultSource 9,241        0.0       0         0        
3      scr299    AreaSource         1,572        0.0       0         0        
0      i17       ComplexFaultSource 33,383       0.0       0         0        
2      sh6       AreaSource         12,900       0.0       0         0        
4      s72       AreaSource         17,871       0.0       0         0        
2      sh14      AreaSource         41,952       0.0       0         0        
4      s35       AreaSource         12,327       0.0       0         0        
4      s70       AreaSource         17,871       0.0       0         0        
4      s34       AreaSource         12,327       0.0       0         0        
3      scr301    AreaSource         17,268       0.0       0         0        
4      s13       AreaSource         12,726       0.0       0         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.002     16    
ComplexFaultSource 0.0       2     
================== ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.007 0.003  0.003 0.011 9        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   4.632     0.0       1     
total count_eff_ruptures         0.059     0.020     9     
managing sources                 0.010     0.0       1     
store source_info                6.247E-04 0.0       1     
aggregate curves                 1.175E-04 0.0       9     
filtering composite source model 6.008E-05 0.0       1     
reading site collection          3.242E-05 0.0       1     
saving probability maps          2.456E-05 0.0       1     
================================ ========= ========= ======