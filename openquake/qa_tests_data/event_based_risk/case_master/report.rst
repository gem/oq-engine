event based risk
================

============== ===================
checksum32     4,227,350,644      
date           2019-03-14T01:46:12
engine_version 3.4.0-gita06742ffe6
============== ===================

num_sites = 7, num_levels = 46, num_rlzs = 8

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
b1        0.25000 complex(2,0,2)  4               
b2        0.75000 complex(2,0,2)  4               
========= ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================== =========== ======================= =================
grp_id gsims                                                          distances   siteparams              ruptparams       
====== ============================================================== =========== ======================= =================
0      '[BooreAtkinson2008]' '[ChiouYoungs2008]'                      rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
1      '[AkkarBommer2010]\nminimum_distance = 10' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
2      '[BooreAtkinson2008]' '[ChiouYoungs2008]'                      rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
3      '[AkkarBommer2010]\nminimum_distance = 10' '[ChiouYoungs2008]' rjb rrup rx vs30 vs30measured z1pt0 dip mag rake ztor
====== ============================================================== =========== ======================= =================

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,'[BooreAtkinson2008]': [0 1]
  0,'[ChiouYoungs2008]': [2 3]
  1,'[AkkarBommer2010]\nminimum_distance = 10': [0 2]
  1,'[ChiouYoungs2008]': [1 3]
  2,'[BooreAtkinson2008]': [4 5]
  2,'[ChiouYoungs2008]': [6 7]
  3,'[AkkarBommer2010]\nminimum_distance = 10': [4 6]
  3,'[ChiouYoungs2008]': [5 7]>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== ============ ============
source_model       grp_id trt                  eff_ruptures tot_ruptures
================== ====== ==================== ============ ============
source_model_1.xml 0      Active Shallow Crust 482          482         
source_model_1.xml 1      Stable Shallow Crust 4            4           
source_model_2.xml 2      Active Shallow Crust 482          482         
source_model_2.xml 3      Stable Shallow Crust 1            1           
================== ====== ==================== ============ ============

============= =====
#TRT models   4    
#eff_ruptures 969  
#tot_ruptures 969  
#tot_weight   2,564
============= =====

Estimated data transfer for the avglosses
-----------------------------------------
7 asset(s) x 8 realization(s) x 5 loss type(s) x 2 losses x 8 bytes x 30 tasks = 131.25 KB

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
0      1         S    0     2     482          0.03915   0.0        7.00000   1         0.0    
2      1         S    4     6     482          0.03817   0.0        7.00000   1         0.0    
1      2         S    2     4     4            0.00199   0.0        7.00000   1         2.00000
3      2         X    6     402   1            2.363E-04 0.0        7.00000   1         0.0    
====== ========= ==== ===== ===== ============ ========= ========== ========= ========= =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.07931   3     
X    2.363E-04 1     
==== ========= ======

Duplicated sources
------------------
['1']
Found 2 source(s) with the same ID and 1 true duplicate(s)
Here is a fake duplicate: 2

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =======
operation-duration mean      stddev    min       max       outputs
read_source_models 0.00764   0.00381   0.00495   0.01034   2      
only_filter        0.00494   9.331E-04 0.00428   0.00560   2      
sample_ruptures    0.02093   0.02109   6.981E-04 0.03963   4      
get_eid_rlz        4.979E-04 1.729E-05 4.787E-04 5.124E-04 3      
================== ========= ========= ========= ========= =======

Data transfer
-------------
================== =============================================== ========
task               sent                                            received
read_source_models converter=626 B fnames=240 B                    13.94 KB
only_filter        srcs=12.85 KB srcfilter=506 B dummy=28 B        13.12 KB
sample_ruptures    param=21.98 KB sources=14.63 KB srcfilter=880 B 2.26 KB 
get_eid_rlz        self=5 KB                                       1.04 KB 
================== =============================================== ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
total sample_ruptures    0.08371  1.66016   4     
iter_ruptures            0.07865  0.0       4     
total read_source_models 0.01529  0.19141   2     
total only_filter        0.00987  1.44531   2     
store source model       0.00571  0.0       2     
saving ruptures          0.00287  0.0       1     
store source_info        0.00192  0.0       1     
total get_eid_rlz        0.00149  0.0       3     
reading exposure         0.00116  0.0       1     
======================== ======== ========= ======