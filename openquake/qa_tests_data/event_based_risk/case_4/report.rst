Event Based Hazard for Turkey reduced
=====================================

num_sites = 14, sitecol = 1.25 KB

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 0          
maximum_distance             200        
investigation_time           10         
ses_per_logic_tree_path      1          
truncation_level             3.000      
rupture_mesh_spacing         2.000      
complex_fault_mesh_spacing   2.000      
width_of_mfd_bin             0.100      
area_source_discretization   10         
random_seed                  323        
master_seed                  0          
concurrent_tasks             64         
============================ ===========

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure.xml <exposure.xml>`_                                            
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job_h.ini <job_h.ini>`_                                                  
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `as_model.xml <as_model.xml>`_                                            
source                   `fsbg_model.xml <fsbg_model.xml>`_                                        
source                   `ss_model.xml <ss_model.xml>`_                                            
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ====== ======================================================== ====================== ================
smlt_path                weight source_model_file                                        gsim_logic_tree        num_realizations
======================== ====== ======================================================== ====================== ================
AreaSource               0.500  `models/src/as_model.xml <models/src/as_model.xml>`_     simple(0,0,0,0,0,4,0)  4/4             
FaultSourceAndBackground 0.200  `models/src/fsbg_model.xml <models/src/fsbg_model.xml>`_ simple(0,0,0,0,0,4,0)  4/4             
SeiFaCrust               0.300  `models/src/ss_model.xml <models/src/ss_model.xml>`_     trivial(0,0,0,0,0,0,0) 0/0             
======================== ====== ======================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================================================== ================= ======================= ============================
trt_id gsims                                                              distances         siteparams              ruptparams                  
====== ================================================================== ================= ======================= ============================
5      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
9      AkkarBommer2010 CauzziFaccioli2008 ChiouYoungs2008 ZhaoEtAl2006Asc rhypo rx rjb rrup vs30measured z1pt0 vs30 ztor mag hypo_depth rake dip
====== ================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  5,AkkarBommer2010: ['<0,AreaSource,AkkarBommer2010asc_@_@_@_@_@_@,w=0.25>']
  5,CauzziFaccioli2008: ['<1,AreaSource,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.25>']
  5,ChiouYoungs2008: ['<2,AreaSource,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.142857142857>']
  5,ZhaoEtAl2006Asc: ['<3,AreaSource,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0714285714286>']
  9,AkkarBommer2010: ['<4,FaultSourceAndBackground,AkkarBommer2010asc_@_@_@_@_@_@,w=0.1>']
  9,CauzziFaccioli2008: ['<5,FaultSourceAndBackground,CauzziFaccioli2008asc_@_@_@_@_@_@,w=0.1>']
  9,ChiouYoungs2008: ['<6,FaultSourceAndBackground,ChiouYoungs2008asc_@_@_@_@_@_@,w=0.0571428571429>']
  9,ZhaoEtAl2006Asc: ['<7,FaultSourceAndBackground,ZhaoEtAl2006Ascasc_@_@_@_@_@_@,w=0.0285714285714>']>

Non-empty rupture collections
-----------------------------
=== ======================== ==================== ============
col smlt_path                TRT                  num_ruptures
=== ======================== ==================== ============
5   AreaSource               Active Shallow Crust 25          
9   FaultSourceAndBackground Active Shallow Crust 11          
=== ======================== ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
5           0 1 2 3     
9           4 5 6 7     
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 10       
Sent data                   18.47 MB 
Total received data         104.35 KB
Maximum received per task   25.41 KB 
=========================== =========

Exposure model
--------------
=========== ==
#assets     14
#taxonomies 9 
=========== ==

======== =======
Taxonomy #Assets
======== =======
RC_HR    1      
RC_LR    3      
RC_MR    1      
SAM_1S   1      
SAM_2S   2      
SAM_3S   1      
SAM_4S   1      
URM_1S   2      
URM_2S   2      
======== =======

Slowest sources
---------------
============ ============ ================= ====== ========= =========== ========== =========
trt_model_id source_id    source_class      weight split_num filter_time split_time calc_time
============ ============ ================= ====== ========= =========== ========== =========
5            AS_GEAS343   AreaSource        625    1         0.002       0.0        9.174    
9            FSBG_TRBG103 AreaSource        282    1         0.001       0.0        6.228    
5            AS_TRAS334   AreaSource        244    1         0.001       0.0        5.222    
5            AS_AMAS453   AreaSource        175    1         0.001       0.0        4.086    
5            AS_TRAS346   AreaSource        154    1         0.001       0.0        2.694    
5            AS_TRAS360   AreaSource        182    1         0.001       0.0        2.414    
5            AS_TRAS458   AreaSource        121    1         0.001       0.0        1.574    
5            AS_TRAS395   AreaSource        122    1         0.001       0.0        1.445    
5            AS_TRAS410   AreaSource        81     1         0.001       0.0        1.034    
5            AS_GEAS479   AreaSource        72     1         0.002       0.0        0.960    
9            FSBG_TRBG989 AreaSource        33     1         0.001       0.0        0.574    
9            FSBG_TRCS439 SimpleFaultSource 392    1         0.003       0.0        0.427    
9            FSBG_TRCS114 SimpleFaultSource 958    1         0.003       0.0        0.349    
9            FSBG_TRCS082 SimpleFaultSource 412    1         0.003       0.0        0.259    
9            FSBG_TRCS322 SimpleFaultSource 374    1         0.003       0.0        0.190    
9            FSBG_TRCS113 SimpleFaultSource 413    1         0.003       0.0        0.188    
9            FSBG_TRCS003 SimpleFaultSource 2,026  1,854     0.010       2.417      0.180    
9            FSBG_TRCS141 SimpleFaultSource 248    1         0.003       0.0        0.148    
9            FSBG_TRCS373 SimpleFaultSource 130    1         0.003       0.0        0.146    
9            FSBG_TRCS239 SimpleFaultSource 222    1         0.004       0.0        0.129    
============ ============ ================= ====== ========= =========== ========== =========