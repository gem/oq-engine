Event Based Risk Lisbon
=======================

=============================================== ========================
tstation.gem.lan:/mnt/ssd/oqdata/calc_1796.hdf5 Fri Jul  7 07:32:20 2017
checksum32                                      887,297,220             
engine_version                                  2.6.0-git50066b9        
=============================================== ========================

num_sites = 1, num_imts = 1

Parameters
----------
=============================== ==================
calculation_mode                'event_based_risk'
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 400.0}
investigation_time              2.0               
ses_per_logic_tree_path         1                 
truncation_level                5.0               
rupture_mesh_spacing            4.0               
complex_fault_mesh_spacing      4.0               
width_of_mfd_bin                0.1               
area_source_discretization      10.0              
ground_motion_correlation_model None              
random_seed                     23                
master_seed                     42                
avg_losses                      True              
=============================== ==================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model_1asset.xml <exposure_model_1asset.xml>`_    
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_                
source                   `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_                
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model2013.xml <vulnerability_model2013.xml>`_
======================== ============================================================

Composite source model
----------------------
========= ====== ============================================ =============== ================
smlt_path weight source_model_file                            gsim_logic_tree num_realizations
========= ====== ============================================ =============== ================
b1        0.600  `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ complex(2,2)    4/4             
b2        0.400  `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ complex(2,2)    4/4             
========= ====== ============================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
grp_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
1      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
2      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
3      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       mag rake  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=8, rlzs=8)
  0,AkkarBommer2010(): ['<2,b1~b2_b3,w=0.1260000012516975>', '<3,b1~b2_b4,w=0.054000000536441786>']
  0,AtkinsonBoore2006(): ['<0,b1~b1_b3,w=0.2940000029206275>', '<1,b1~b1_b4,w=0.1260000012516975>']
  1,AkkarBommer2010(): ['<1,b1~b1_b4,w=0.1260000012516975>', '<3,b1~b2_b4,w=0.054000000536441786>']
  1,AtkinsonBoore2006(): ['<0,b1~b1_b3,w=0.2940000029206275>', '<2,b1~b2_b3,w=0.1260000012516975>']
  2,AkkarBommer2010(): ['<6,b2~b2_b3,w=0.0839999987483025>', '<7,b2~b2_b4,w=0.03599999946355822>']
  2,AtkinsonBoore2006(): ['<4,b2~b1_b3,w=0.1959999970793725>', '<5,b2~b1_b4,w=0.0839999987483025>']
  3,AkkarBommer2010(): ['<5,b2~b1_b4,w=0.0839999987483025>', '<7,b2~b2_b4,w=0.03599999946355822>']
  3,AtkinsonBoore2006(): ['<4,b2~b1_b3,w=0.1959999970793725>', '<6,b2~b2_b3,w=0.0839999987483025>']>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== =========== ============ ============
source_model        grp_id trt                  num_sources eff_ruptures tot_ruptures
=================== ====== ==================== =========== ============ ============
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3           36196        48,521      
SA_RA_CATAL1_00.xml 1      Stable Shallow Crust 8           21381        21,381      
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3           36196        48,521      
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 8           21381        21,381      
=================== ====== ==================== =========== ============ ============

============= =======
#TRT models   4      
#sources      22     
#eff_ruptures 115,154
#tot_ruptures 139,804
#tot_weight   0      
============= =======

Informational data
------------------
============================ ======================================================================================
compute_ruptures.received    tot 49.91 KB, max_per_task 5.9 KB                                                     
compute_ruptures.sent        sources 988.43 KB, param 16.03 KB, src_filter 12.02 KB, monitor 5.62 KB, gsims 3.15 KB
hazard.input_weight          13980.399999999998                                                                    
hazard.n_imts                1                                                                                     
hazard.n_levels              40                                                                                    
hazard.n_realizations        8                                                                                     
hazard.n_sites               1                                                                                     
hazard.n_sources             22                                                                                    
hazard.output_weight         40.0                                                                                  
hostname                     tstation.gem.lan                                                                      
require_epsilons             False                                                                                 
============================ ======================================================================================

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 8 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 1 KB

Exposure model
--------------
=============== ========
#assets         1       
#taxonomies     1       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
M1_2_PC  1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
1      5         AreaSource   2,349        0.0       1         0        
0      1         AreaSource   4,163        0.0       1         0        
1      4         AreaSource   1,280        0.0       1         0        
2      0         AreaSource   24,435       0.0       1         0        
3      3         AreaSource   3,509        0.0       1         0        
2      1         AreaSource   4,163        0.0       1         0        
1      7         AreaSource   1,690        0.0       1         0        
3      10        AreaSource   4,482        0.0       1         0        
1      10        AreaSource   4,482        0.0       1         0        
2      2         AreaSource   19,923       0.0       1         0        
3      5         AreaSource   2,349        0.0       1         0        
3      6         AreaSource   4,123        0.0       1         0        
0      2         AreaSource   19,923       0.0       1         0        
3      9         AreaSource   2,508        0.0       1         0        
1      6         AreaSource   4,123        0.0       1         0        
1      8         AreaSource   1,440        0.0       1         0        
3      8         AreaSource   1,440        0.0       1         0        
3      4         AreaSource   1,280        0.0       1         0        
0      0         AreaSource   24,435       0.0       1         0        
1      9         AreaSource   2,508        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       22    
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   1.649 0.663  0.314 2.515 18       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         29        0.730     18    
managing sources               0.917     0.0       1     
reading composite source model 0.824     0.0       1     
saving ruptures                0.028     0.0       18    
prefiltering source model      0.012     0.0       1     
store source_info              0.008     0.0       1     
setting event years            0.006     0.0       1     
reading exposure               0.005     0.0       1     
filtering ruptures             0.003     0.0       12    
reading site collection        4.530E-06 0.0       1     
============================== ========= ========= ======