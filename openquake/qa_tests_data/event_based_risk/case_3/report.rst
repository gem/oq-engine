Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_41591.hdf5 updated Tue Aug 23 17:46:27 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================================================
calculation_mode             'event_based_risk'                                              
number_of_logic_tree_samples 0                                                               
maximum_distance             {u'Stable Shallow Crust': 400.0, u'Active Shallow Crust': 400.0}
investigation_time           2.0                                                             
ses_per_logic_tree_path      1                                                               
truncation_level             5.0                                                             
rupture_mesh_spacing         4.0                                                             
complex_fault_mesh_spacing   4.0                                                             
width_of_mfd_bin             0.1                                                             
area_source_discretization   10.0                                                            
random_seed                  23                                                              
master_seed                  42                                                              
avg_losses                   False                                                           
engine_version               '2.1.0-git5b04a6e'                                              
============================ ================================================================

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
b1        0.600  `SA_RA_CATAL1_00.xml <SA_RA_CATAL1_00.xml>`_ complex(2,2)    2/2             
b2        0.400  `SA_RA_CATAL2_00.xml <SA_RA_CATAL2_00.xml>`_ complex(2,2)    4/4             
========= ====== ============================================ =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ===================================== ========= ========== ==========
grp_id gsims                                 distances siteparams ruptparams
====== ===================================== ========= ========== ==========
0      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
2      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
3      AkkarBommer2010() AtkinsonBoore2006() rjb rrup  vs30       rake mag  
====== ===================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,AkkarBommer2010(): ['<1,b1~b2_@,w=0.180000001788>']
  0,AtkinsonBoore2006(): ['<0,b1~b1_@,w=0.420000004172>']
  2,AkkarBommer2010(): ['<4,b2~b2_b3,w=0.0839999987483>', '<5,b2~b2_b4,w=0.0359999994636>']
  2,AtkinsonBoore2006(): ['<2,b2~b1_b3,w=0.195999997079>', '<3,b2~b1_b4,w=0.0839999987483>']
  3,AkkarBommer2010(): ['<3,b2~b1_b4,w=0.0839999987483>', '<5,b2~b2_b4,w=0.0359999994636>']
  3,AtkinsonBoore2006(): ['<2,b2~b1_b3,w=0.195999997079>', '<4,b2~b2_b3,w=0.0839999987483>']>

Number of ruptures per tectonic region type
-------------------------------------------
=================== ====== ==================== =========== ============ ======
source_model        grp_id trt                  num_sources eff_ruptures weight
=================== ====== ==================== =========== ============ ======
SA_RA_CATAL1_00.xml 0      Active Shallow Crust 3           4            1,213 
SA_RA_CATAL2_00.xml 2      Active Shallow Crust 3           6            1,213 
SA_RA_CATAL2_00.xml 3      Stable Shallow Crust 8           3            534   
=================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        14   
#eff_ruptures   13   
filtered_weight 2,961
=============== =====

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 7,611       
compute_ruptures_num_tasks             20          
compute_ruptures_sent.monitor          24,020      
compute_ruptures_sent.rlzs_by_gsim     18,940      
compute_ruptures_sent.sitecol          8,660       
compute_ruptures_sent.sources          1,193,154   
compute_ruptures_tot_received          84,172      
hazard.input_weight                    3,495       
hazard.n_imts                          1           
hazard.n_levels                        40          
hazard.n_realizations                  8           
hazard.n_sites                         1           
hazard.n_sources                       22          
hazard.output_weight                   320         
hostname                               gem-tstation
require_epsilons                       1           
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 13   
Total number of events   13   
Rupture multiplicity     1.000
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for src_group_id=2, contains 1 IMT(s), 4 realization(s)
and has a size of 96 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
1 asset(s) x 6 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 16 tasks = 768 B

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
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            0         AreaSource   610    543       0.002       0.181      6.614         0.038         543      
2            0         AreaSource   610    543       0.001       0.148      6.500         0.015         543      
0            2         AreaSource   498    687       9.699E-04   0.136      2.116         0.009         262      
2            2         AreaSource   498    687       9.720E-04   0.171      2.037         0.009         262      
3            10        AreaSource   112    1         7.060E-04   0.0        1.122         1.122         1        
1            10        AreaSource   112    1         7.639E-04   0.0        1.118         1.118         1        
2            1         AreaSource   104    1         7.329E-04   0.0        1.065         1.065         1        
0            1         AreaSource   104    1         8.230E-04   0.0        1.050         1.050         1        
1            6         AreaSource   103    1         7.460E-04   0.0        0.931         0.931         1        
3            6         AreaSource   103    1         7.510E-04   0.0        0.927         0.927         1        
1            3         AreaSource   87     1         7.670E-04   0.0        0.768         0.768         1        
3            3         AreaSource   87     1         7.241E-04   0.0        0.753         0.753         1        
3            9         AreaSource   62     1         7.510E-04   0.0        0.606         0.606         1        
1            9         AreaSource   62     1         7.238E-04   0.0        0.581         0.581         1        
1            5         AreaSource   58     1         7.250E-04   0.0        0.573         0.573         1        
3            5         AreaSource   58     1         7.830E-04   0.0        0.538         0.538         1        
3            7         AreaSource   42     1         7.160E-04   0.0        0.464         0.464         1        
1            7         AreaSource   42     1         7.210E-04   0.0        0.415         0.415         1        
1            4         AreaSource   32     1         7.381E-04   0.0        0.389         0.389         1        
3            8         AreaSource   36     1         7.639E-04   0.0        0.358         0.358         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.019       0.636      29            12            1,628     22    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         1.483 0.767  0.002 2.459 20       
compute_ruptures.memory_mb        0.081 0.156  0.0   0.422 20       
compute_gmfs_and_curves.time_sec  0.007 0.002  0.004 0.010 13       
compute_gmfs_and_curves.memory_mb 0.151 0.213  0.0   0.605 13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         29        0.422     20    
reading composite source model 0.930     0.0       1     
managing sources               0.844     0.0       1     
splitting sources              0.636     0.0       4     
total compute_gmfs_and_curves  0.091     0.605     13    
compute poes                   0.075     0.0       13    
store source_info              0.042     0.0       1     
saving gmfs                    0.020     0.0       44    
filtering sources              0.019     0.0       22    
saving ruptures                0.013     0.0       1     
make contexts                  0.012     0.0       13    
aggregate curves               0.006     0.0       20    
filtering ruptures             0.003     0.0       14    
reading exposure               0.003     0.0       1     
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======