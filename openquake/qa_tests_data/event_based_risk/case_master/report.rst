event based risk
================

============== ===================
checksum32     588,634,913        
date           2018-12-13T12:57:45
engine_version 3.3.0-git68d7d11268
============== ===================

num_sites = 7, num_levels = 46

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         10                
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model 'JB2009'          
minimum_intensity               {}                
random_seed                     24                
master_seed                     0                 
ses_seed                        42                
avg_losses                      True              
=============================== ==================

Input files
-----------
=================================== ================================================================================
Name                                File                                                                            
=================================== ================================================================================
business_interruption_vulnerability `downtime_vulnerability_model.xml <downtime_vulnerability_model.xml>`_          
contents_vulnerability              `contents_vulnerability_model.xml <contents_vulnerability_model.xml>`_          
exposure                            `exposure_model.xml <exposure_model.xml>`_                                      
gsim_logic_tree                     `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                                    
job_ini                             `job.ini <job.ini>`_                                                            
nonstructural_vulnerability         `nonstructural_vulnerability_model.xml <nonstructural_vulnerability_model.xml>`_
occupants_vulnerability             `occupants_vulnerability_model.xml <occupants_vulnerability_model.xml>`_        
source_model_logic_tree             `ssmLT.xml <ssmLT.xml>`_                                                        
structural_vulnerability            `structural_vulnerability_model.xml <structural_vulnerability_model.xml>`_      
=================================== ================================================================================

Composite source model
----------------------
========= ======= =============== ================
smlt_path weight  gsim_logic_tree num_realizations
========= ======= =============== ================
b1        0.25000 complex(2,2,1)  4/4             
b2        0.25000 complex(2,2,1)  4/4             
b3        0.50000 complex(2,2,1)  1/1             
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== =========== ======================= =================
grp_id gsims                                 distances   siteparams              ruptparams       
====== ===================================== =========== ======================= =================
0      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      BooreAtkinson2008() ChiouYoungs2008() rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      AkkarBommer2010() ChiouYoungs2008()   rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
4      MontalvaEtAl2017SSlab()               rhypo rrup  backarc vs30            hypo_depth mag   
====== ===================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=9, rlzs=9)
  0,BooreAtkinson2008(): [0 1]
  0,ChiouYoungs2008(): [2 3]
  1,AkkarBommer2010(): [0 2]
  1,ChiouYoungs2008(): [1 3]
  2,BooreAtkinson2008(): [4 5]
  2,ChiouYoungs2008(): [6 7]
  3,AkkarBommer2010(): [4 6]
  3,ChiouYoungs2008(): [5 7]
  4,MontalvaEtAl2017SSlab(): [8]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
6.05.hdf5          4      Deep Seismicity      2            2           
================== ====== ==================== ============ ============

============= ===
#TRT models   5  
#eff_ruptures 971
#tot_ruptures 971
#tot_weight   971
============= ===

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 9 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 60 tasks = 295.31 KB

Exposure model
--------------
=============== ========
#assets         7       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ======= ====== === === ========= ==========
taxonomy mean    stddev min max num_sites num_assets
tax1     1.00000 0.0    1   1   4         4         
tax2     1.00000 0.0    1   1   2         2         
tax3     1.00000 NaN    1   1   1         1         
*ALL*    1.00000 0.0    1   1   7         7         
======== ======= ====== === === ========= ==========

Slowest sources
---------------
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
grp_id source_id code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight 
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======
0      1         S    0     2     482          0.05176   0.0        7.00000   1         0.0    
1      2         S    2     4     4            0.00430   0.0        7.00000   1         2.00000
2      1         S    0     2     482          0.05039   0.0        7.00000   1         0.0    
3      2         X    2     398   1            5.028E-04 0.0        7.00000   1         0.0    
4      buc06pt05 N    0     24    2            3.409E-04 0.0        7.00000   1         2.00000
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
N    3.409E-04 1     
S    0.10645   3     
X    5.028E-04 1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =======
operation-duration mean      stddev    min       max       outputs
read_source_models 0.01189   0.00609   0.00612   0.01825   3      
split_filter       0.01316   NaN       0.01316   0.01316   1      
sample_ruptures    0.02205   0.02695   9.265E-04 0.05219   5      
get_eid_rlz        5.804E-04 1.327E-04 4.299E-04 7.260E-04 4      
================== ========= ========= ========= ========= =======

Data transfer
-------------
================== ======================================== ========
task               sent                                     received
read_source_models converter=1.14 KB fnames=351 B           16.26 KB
split_filter       srcs=13.91 KB srcfilter=253 B dummy=14 B 14.21 KB
sample_ruptures    param=27.42 KB sources=16.71 KB          3.44 KB 
get_eid_rlz        self=6.48 KB                             1.3 KB  
================== ======================================== ========

Slowest operations
------------------
======================== ========= ========= ======
operation                time_sec  memory_mb counts
======================== ========= ========= ======
total sample_ruptures    0.11025   0.35156   5     
iter_ruptures            0.10593   0.0       5     
total read_source_models 0.03566   0.0       3     
total only_filter        0.01316   0.0       1     
store source model       0.00685   0.0       3     
saving ruptures          0.00482   0.0       2     
store source_info        0.00236   0.0       1     
total get_eid_rlz        0.00232   0.0       4     
reading exposure         8.967E-04 0.0       1     
======================== ========= ========= ======