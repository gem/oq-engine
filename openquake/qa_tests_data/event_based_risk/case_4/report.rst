Event Based Hazard for Turkey reduced
=====================================

gem-tstation:/home/michele/ssd/calc_12018.hdf5 updated Fri Apr 22 04:10:14 2016

num_sites = 14, sitecol = 1.31 KB

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           10.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.1                
area_source_discretization   10.0               
random_seed                  323                
master_seed                  0                  
oqlite_version               '0.13.0-gitd746861'
============================ ===================

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

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ======
source_model              trt_id trt                  num_sources eff_ruptures weight
========================= ====== ==================== =========== ============ ======
models/src/as_model.xml   5      Active Shallow Crust 9           25           1,779 
models/src/fsbg_model.xml 9      Active Shallow Crust 26          11           6,908 
========================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        35   
#eff_ruptures   36   
filtered_weight 8,687
=============== =====

Informational data
------------------
================ ==============
hostname         'gem-tstation'
require_epsilons False         
================ ==============

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
5            AS_GEAS343   AreaSource        625    1         0.002       0.0        6.229    
9            FSBG_TRBG103 AreaSource        282    1         0.001       0.0        2.824    
5            AS_TRAS334   AreaSource        244    1         0.001       0.0        2.351    
5            AS_AMAS453   AreaSource        175    1         0.001       0.0        2.031    
5            AS_TRAS360   AreaSource        182    1         7.942E-04   0.0        1.898    
5            AS_TRAS346   AreaSource        154    1         9.489E-04   0.0        1.407    
5            AS_TRAS395   AreaSource        122    1         8.070E-04   0.0        1.138    
5            AS_TRAS458   AreaSource        121    1         7.691E-04   0.0        1.111    
5            AS_GEAS479   AreaSource        72     1         0.001       0.0        0.831    
5            AS_TRAS410   AreaSource        81     1         7.858E-04   0.0        0.738    
9            FSBG_TRBG989 AreaSource        33     1         8.628E-04   0.0        0.316    
9            FSBG_TRCS114 SimpleFaultSource 958    1         0.002       0.0        0.176    
9            FSBG_TRCS003 SimpleFaultSource 2,026  1,854     0.004       1.014      0.158    
9            FSBG_TRCS439 SimpleFaultSource 392    1         0.002       0.0        0.132    
9            FSBG_TRCS141 SimpleFaultSource 248    1         0.002       0.0        0.071    
9            FSBG_TRCS113 SimpleFaultSource 413    1         0.002       0.0        0.066    
9            FSBG_TRCS437 SimpleFaultSource 390    1         0.002       0.0        0.064    
9            FSBG_TRCS068 SimpleFaultSource 308    1         0.002       0.0        0.059    
9            FSBG_TRCS239 SimpleFaultSource 222    1         0.003       0.0        0.058    
9            FSBG_TRCS082 SimpleFaultSource 412    1         0.002       0.0        0.054    
============ ============ ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         22        0.367     18    
reading composite source model 9.273     0.0       1     
managing sources               2.073     0.0       1     
splitting sources              1.014     0.0       1     
total compute_gmfs_and_curves  0.445     0.004     36    
filtering sources              0.243     0.0       155   
bulding hazard curves          0.223     0.0       36    
compute poes                   0.153     0.0       36    
aggregating hcurves            0.098     0.0       144   
make contexts                  0.049     0.0       36    
saving gmfs                    0.042     0.0       36    
store source_info              0.042     0.0       1     
saving ruptures                0.023     0.0       1     
aggregate curves               0.015     0.0       162   
filtering ruptures             0.012     0.0       53    
reading exposure               0.010     0.0       1     
reading site collection        7.868E-06 0.0       1     
============================== ========= ========= ======