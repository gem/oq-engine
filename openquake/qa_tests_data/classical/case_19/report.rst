SHARE OpenQuake Computational Settings
======================================

============== ===================
checksum32     1,220,765,868      
date           2018-03-26T15:56:16
engine_version 2.10.0-git543cfb0  
============== ===================

num_sites = 1, num_levels = 78

Parameters
----------
=============================== ===========================================
calculation_mode                'classical'                                
number_of_logic_tree_samples    0                                          
maximum_distance                {'default': [(6, 100), (7, 150), (9, 200)]}
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
========= ====== ====================== ================
smlt_path weight gsim_logic_tree        num_realizations
========= ====== ====================== ================
b1        1.000  complex(4,2,1,5,0,0,4) 4/4             
========= ====== ====================== ================

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
  4,AtkinsonBoore2003SSlab(): [0]
  4,LinLee2008SSlab(): [1]
  4,YoungsEtAl1997SSlab(): [2]
  4,ZhaoEtAl2006SSlab(): [3]>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= ============ ============
source_model                 grp_id trt               eff_ruptures tot_ruptures
============================ ====== ================= ============ ============
simple_area_source_model.xml 4      Subduction Inslab 7,770        93,219      
============================ ====== ================= ============ ============

Slowest sources
---------------
========= ================== ============ ========= ========== ========= =========
source_id source_class       num_ruptures calc_time split_time num_sites num_split
========= ================== ============ ========= ========== ========= =========
s46       AreaSource         7,770        0.183     0.069      370       370      
scr301    AreaSource         17,268       0.0       0.344      0         0        
sh14      AreaSource         41,952       0.0       0.603      0         0        
scr293    AreaSource         61,740       0.0       1.421      0         0        
s40       AreaSource         12,327       0.0       0.095      0         0        
s13       AreaSource         12,726       0.0       0.105      0         0        
i20       ComplexFaultSource 9,241        0.0       7.246E-04  0         0        
sh6       AreaSource         12,900       0.0       0.189      0         0        
s72       AreaSource         17,871       0.0       0.157      0         0        
v1        AreaSource         42           0.0       0.002      0         0        
sh13      AreaSource         41,952       0.0       0.594      0         0        
scr299    AreaSource         1,572        0.0       0.023      0         0        
scr304    AreaSource         574          0.0       0.007      0         0        
i17       ComplexFaultSource 33,383       0.0       0.002      0         0        
v4        AreaSource         168          0.0       0.004      0         0        
s34       AreaSource         12,327       0.0       0.096      0         0        
s70       AreaSource         17,871       0.0       0.152      0         0        
s35       AreaSource         12,327       0.0       0.096      0         0        
========= ================== ============ ========= ========== ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.183     16    
ComplexFaultSource 0.0       2     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.008 0.003  0.003 0.012 34       
================== ===== ====== ===== ===== =========

Informational data
------------------
============== =================================================================================== ========
task           sent                                                                                received
count_ruptures sources=111.57 KB param=38.78 KB srcfilter=24.57 KB gsims=12.88 KB monitor=10.96 KB 12.15 KB
============== =================================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 9.505     0.0       1     
splitting sources              3.968     0.0       1     
managing sources               3.803     0.0       1     
total count_ruptures           0.263     1.941     34    
store source_info              0.018     0.0       1     
unpickling count_ruptures      0.002     0.0       34    
aggregate curves               7.370E-04 0.0       34    
reading site collection        3.188E-04 0.0       1     
saving probability maps        3.076E-05 0.0       1     
============================== ========= ========= ======