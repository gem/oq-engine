Classical Tiling for Turkey reduced
===================================

============== ===================
checksum32     1,556,025,092      
date           2018-02-02T16:04:45
engine_version 2.9.0-gitd6a3184   
============== ===================

num_sites = 83, num_levels = 90

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 100.0}
investigation_time              10.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                0.1               
area_source_discretization      25.0              
ground_motion_correlation_model None              
random_seed                     323               
master_seed                     0                 
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                              
job_ini                  `job.ini <job.ini>`_                                                      
site_model               `site_model.xml <site_model.xml>`_                                        
source                   `as_model.xml <as_model.xml>`_                                            
source                   `fsbg_model.xml <fsbg_model.xml>`_                                        
source                   `ss_model.xml <ss_model.xml>`_                                            
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_              
structural_vulnerability `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_
======================== ==========================================================================

Composite source model
----------------------
======================== ====== ====================== ================
smlt_path                weight gsim_logic_tree        num_realizations
======================== ====== ====================== ================
AreaSource               0.500  complex(1,2,4,4,0,5,4) 4/4             
FaultSourceAndBackground 0.200  complex(1,2,4,4,0,5,4) 4/4             
SeiFaCrust               0.300  complex(1,2,4,4,0,5,4) 0/0             
======================== ====== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================== ================= ======================= ============================
grp_id gsims                                                                      distances         siteparams              ruptparams                  
====== ========================================================================== ================= ======================= ============================
4      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
9      AkkarBommer2010() CauzziFaccioli2008() ChiouYoungs2008() ZhaoEtAl2006Asc() rhypo rjb rrup rx vs30 vs30measured z1pt0 dip hypo_depth mag rake ztor
====== ========================================================================== ================= ======================= ============================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  4,AkkarBommer2010(): [0]
  4,CauzziFaccioli2008(): [1]
  4,ChiouYoungs2008(): [2]
  4,ZhaoEtAl2006Asc(): [3]
  9,AkkarBommer2010(): [4]
  9,CauzziFaccioli2008(): [5]
  9,ChiouYoungs2008(): [6]
  9,ZhaoEtAl2006Asc(): [7]>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== ============ ============
source_model              grp_id trt                  eff_ruptures tot_ruptures
========================= ====== ==================== ============ ============
models/src/as_model.xml   4      Active Shallow Crust 19,323       32,481      
models/src/fsbg_model.xml 9      Active Shallow Crust 7,632        16,635      
========================= ====== ==================== ============ ============

============= ======
#tiles        9     
#TRT models   2     
#eff_ruptures 26,955
#tot_ruptures 49,116
#tot_weight   0     
============= ======

Informational data
------------------
======================= ====================================================================================
count_ruptures.received tot 13.15 KB, max_per_task 1.84 KB                                                  
count_ruptures.sent     sources 60.24 KB, param 16.34 KB, srcfilter 16.18 KB, gsims 5.33 KB, monitor 4.36 KB
hazard.input_weight     13439.400000000001                                                                  
hazard.n_imts           2                                                                                   
hazard.n_levels         90                                                                                  
hazard.n_realizations   3840                                                                                
hazard.n_sites          83                                                                                  
hazard.n_sources        31                                                                                  
hazard.output_weight    7470.0                                                                              
hostname                tstation.gem.lan                                                                    
require_epsilons        False                                                                               
======================= ====================================================================================

Slowest sources
---------------
============ ============ ============ ========= ========= =========
source_id    source_class num_ruptures calc_time num_sites num_split
============ ============ ============ ========= ========= =========
AS_GEAS343   AreaSource   3,876        0.029     6,201     138      
FSBG_TRBG103 AreaSource   1,755        0.010     3,510     4        
FSBG_ARAS462 AreaSource   306          0.003     367       2        
FSBG_HRAS215 AreaSource   357          0.0       1         0        
FSBG_HUAS132 AreaSource   630          0.0       1         0        
FSBG_CHAS098 AreaSource   429          0.0       1         0        
AS_IEAS021   AreaSource   16,668       0.0       1         0        
AS_SEAS033   AreaSource   2,808        0.0       1         0        
FSBG_DEAS972 AreaSource   528          0.0       1         0        
AS_PLAS982   AreaSource   1,044        0.0       1         0        
V_CZAS127    AreaSource   42           0.0       1         0        
100041       PointSource  27           0.0       1         0        
AS_BEAS157   AreaSource   36           0.0       1         0        
FSBG_CHAS089 AreaSource   180          0.0       1         0        
AS_ITAS306   AreaSource   6,408        0.0       1         0        
IS_ITID10    AreaSource   18,585       0.0       1         0        
V_CZAS080    AreaSource   14           0.0       1         0        
FSBG_BGBG090 AreaSource   486          0.0       1         0        
FSBG_ITAS307 AreaSource   867          0.0       1         0        
FSBG_ESBG038 AreaSource   675          0.0       1         0        
============ ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.042     29    
ComplexFaultSource 0.0       1     
PointSource        0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_ruptures     0.004 0.001  0.002 0.006 14       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 1.260     0.0       1     
managing sources               0.356     0.0       1     
total count_ruptures           0.057     0.0       14    
store source_info              0.035     0.0       1     
reading site collection        0.005     0.0       1     
aggregate curves               3.064E-04 0.0       14    
saving probability maps        2.551E-05 0.0       1     
============================== ========= ========= ======