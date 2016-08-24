Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_42123.hdf5 updated Wed Aug 24 08:11:53 2016

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
engine_version               '2.1.0-git81d4f3d'                                              
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
compute_ruptures_sent.sources          1,193,222   
compute_ruptures_tot_received          84,160      
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
0            0         AreaSource   610    543       0.002       0.177      6.458         0.031         543      
2            0         AreaSource   610    543       9.339E-04   0.141      6.125         0.013         543      
2            2         AreaSource   498    687       8.879E-04   0.131      2.049         0.009         262      
0            2         AreaSource   498    687       9.179E-04   0.131      2.045         0.027         262      
1            10        AreaSource   112    1         6.721E-04   0.0        1.111         1.111         1        
3            10        AreaSource   112    1         6.690E-04   0.0        1.007         1.007         1        
2            1         AreaSource   104    1         6.499E-04   0.0        1.005         1.005         1        
0            1         AreaSource   104    1         7.589E-04   0.0        0.980         0.980         1        
1            6         AreaSource   103    1         7.579E-04   0.0        0.949         0.949         1        
3            6         AreaSource   103    1         6.630E-04   0.0        0.886         0.886         1        
1            3         AreaSource   87     1         6.599E-04   0.0        0.835         0.835         1        
3            3         AreaSource   87     1         6.800E-04   0.0        0.769         0.769         1        
3            9         AreaSource   62     1         6.521E-04   0.0        0.581         0.581         1        
3            5         AreaSource   58     1         6.590E-04   0.0        0.564         0.564         1        
1            9         AreaSource   62     1         6.390E-04   0.0        0.563         0.563         1        
1            5         AreaSource   58     1         6.580E-04   0.0        0.560         0.560         1        
1            7         AreaSource   42     1         6.330E-04   0.0        0.455         0.455         1        
3            7         AreaSource   42     1         6.340E-04   0.0        0.438         0.438         1        
3            4         AreaSource   32     1         6.399E-04   0.0        0.379         0.379         1        
1            4         AreaSource   32     1         6.680E-04   0.0        0.373         0.373         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.017       0.580      28            12            1,628     22    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         1.446 0.743  0.002 2.353 20       
compute_ruptures.memory_mb        0.008 0.038  0.0   0.168 20       
compute_gmfs_and_curves.time_sec  0.007 0.002  0.005 0.011 13       
compute_gmfs_and_curves.memory_mb 0.153 0.230  0.0   0.664 13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         28        0.168     20    
reading composite source model 0.860     0.0       1     
managing sources               0.789     0.0       1     
splitting sources              0.580     0.0       4     
total compute_gmfs_and_curves  0.096     0.664     13    
compute poes                   0.079     0.0       13    
saving gmfs                    0.067     0.0       44    
store source_info              0.044     0.0       1     
filtering sources              0.017     0.0       22    
saving ruptures                0.014     0.0       1     
make contexts                  0.011     0.0       13    
aggregate curves               0.007     0.0       20    
filtering ruptures             0.003     0.0       14    
reading exposure               0.003     0.0       1     
reading site collection        7.868E-06 0.0       1     
============================== ========= ========= ======