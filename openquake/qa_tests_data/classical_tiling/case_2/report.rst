Classical Tiling for Turkey reduced
===================================

============== ===================
checksum32     567,627,902        
date           2018-04-30T11:23:04
engine_version 3.1.0-gitb0812f0   
============== ===================

num_sites = 14, num_levels = 90

Parameters
----------
=============================== ==================
calculation_mode                'classical'       
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 150.0}
investigation_time              10.0              
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            15.0              
complex_fault_mesh_spacing      15.0              
width_of_mfd_bin                0.1               
area_source_discretization      25.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     323               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================== ==========================================================================
Name                     File                                                                      
======================== ==========================================================================
exposure                 `exposure.xml <exposure.xml>`_                                            
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
======================== ======= ====================== ================
smlt_path                weight  gsim_logic_tree        num_realizations
======================== ======= ====================== ================
AreaSource               0.50000 complex(4,0,2,5,4,4,1) 4/4             
FaultSourceAndBackground 0.20000 complex(4,0,2,5,4,4,1) 4/4             
SeiFaCrust               0.30000 complex(4,0,2,5,4,4,1) 0/0             
======================== ======= ====================== ================

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
===================== ====== ==================== ============ ============
source_model          grp_id trt                  eff_ruptures tot_ruptures
===================== ====== ==================== ============ ============
../src/as_model.xml   4      Active Shallow Crust 2,344        32,481      
../src/fsbg_model.xml 9      Active Shallow Crust 610          16,635      
===================== ====== ==================== ============ ============

============= ======
#tiles        2     
#TRT models   2     
#eff_ruptures 2,955 
#tot_ruptures 49,116
#tot_weight   2,932 
============= ======

Exposure model
--------------
=============== ========
#assets         14      
#taxonomies     9       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
RC_LR    1.00000 0.0    1   1   3         3         
RC_MR    1.00000 NaN    1   1   1         1         
RC_HR    1.00000 NaN    1   1   1         1         
URM_1S   1.00000 0.0    1   1   2         2         
URM_2S   1.00000 0.0    1   1   2         2         
SAM_1S   1.00000 NaN    1   1   1         1         
SAM_2S   1.00000 0.0    1   1   2         2         
SAM_3S   1.00000 NaN    1   1   1         1         
SAM_4S   1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   14        14        
======== ======= ====== === === ========= ==========

Slowest sources
---------------
============== ================== ============ ========= ========== ========= ========= ======
source_id      source_class       num_ruptures calc_time split_time num_sites num_split events
============== ================== ============ ========= ========== ========= ========= ======
FSBG_TRBG103   AreaSource         1,755        0.00445   0.02783    156       69        0     
AS_GEAS343     AreaSource         3,876        0.00236   0.03526    167       71        0     
AS_SEAS033     AreaSource         2,808        0.0       0.01844    0         0         0     
IF_HELL_GRID01 ComplexFaultSource 334          0.0       3.195E-04  0         0         0     
IS_ITID10      AreaSource         18,585       0.0       0.01415    0         0         0     
V_CZAS080      AreaSource         14           0.0       7.186E-04  0         0         0     
AS_NOAS079     AreaSource         23,250       0.0       0.18999    0         0         0     
AS_ZZAS267     AreaSource         5,355        0.0       0.01561    0         0         0     
AS_BEAS157     AreaSource         36           0.0       7.014E-04  0         0         0     
AS_BEAS177     AreaSource         1,638        0.0       0.00975    0         0         0     
AS_IEAS021     AreaSource         16,668       0.0       0.10612    0         0         0     
AS_ITAS306     AreaSource         6,408        0.0       0.03165    0         0         0     
AS_NOAS055     AreaSource         2,952        0.0       0.01945    0         0         0     
AS_PLAS982     AreaSource         1,044        0.0       0.01100    0         0         0     
AS_FIAS032     AreaSource         20,124       0.0       0.12548    0         0         0     
V_CZAS127      AreaSource         42           0.0       0.00118    0         0         0     
FSBG_DEAS972   AreaSource         528          0.0       0.00516    0         0         0     
FSBG_PLAS982   AreaSource         1,044        0.0       0.01113    0         0         0     
AS_PTAS275     AreaSource         5,733        0.0       0.02232    0         0         0     
FSBG_ARAS462   AreaSource         306          0.0       0.00405    0         0         0     
============== ================== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.00681   29    
ComplexFaultSource 0.0       1     
PointSource        0.0       1     
================== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =========
operation-duration mean    stddev  min     max     num_tasks
count_ruptures     0.00617 0.00236 0.00455 0.01135 7        
================== ======= ======= ======= ======= =========

Fastest task
------------
taskno=4, weight=64, duration=0 s, sources="FSBG_TRBG103"

======== ======= ====== === === =
variable mean    stddev min max n
======== ======= ====== === === =
nsites   1.00000 0.0    1   1   6
weight   10      0.0    10  10  6
======== ======= ====== === === =

Slowest task
------------
taskno=3, weight=566, duration=0 s, sources="AS_GEAS343 FSBG_TRBG103"

======== ======= ======= === === ==
variable mean    stddev  min max n 
======== ======= ======= === === ==
nsites   2.63333 0.88992 1   4   30
weight   18      7.78469 10  45  30
======== ======= ======= === === ==

Informational data
------------------
============== ============================================================================== ========
task           sent                                                                           received
count_ruptures sources=36.26 KB param=8.13 KB srcfilter=7.13 KB gsims=2.67 KB monitor=2.26 KB 2.6 KB  
============== ============================================================================== ========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.88503   0.0       1     
splitting sources              0.74726   0.0       1     
managing sources               0.31707   0.0       1     
total count_ruptures           0.04320   2.15625   7     
store source_info              0.03601   0.0       1     
reading site collection        0.01520   0.0       1     
reading exposure               0.00382   0.0       1     
unpickling count_ruptures      2.451E-04 0.0       7     
aggregate curves               1.266E-04 0.0       7     
saving probability maps        2.694E-05 0.0       1     
============================== ========= ========= ======