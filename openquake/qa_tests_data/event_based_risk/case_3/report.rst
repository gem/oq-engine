Event Based Risk Lisbon
=======================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48269.hdf5 updated Wed Sep  7 15:55:53 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

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
compute_ruptures_max_received_per_task 8,836       
compute_ruptures_num_tasks             16          
compute_ruptures_sent.gsims            2,688       
compute_ruptures_sent.monitor          19,888      
compute_ruptures_sent.sitecol          6,928       
compute_ruptures_sent.sources          893,636     
compute_ruptures_tot_received          77,068      
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
0            0         AreaSource   610    543       0.0         0.244      6.692         0.021         543      
2            0         AreaSource   610    543       0.0         0.234      6.490         0.018         543      
0            2         AreaSource   498    262       0.0         0.235      2.193         0.013         262      
2            2         AreaSource   498    262       0.0         0.204      2.154         0.010         262      
1            10        AreaSource   112    0         6.981E-04   0.0        1.209         1.209         1        
3            10        AreaSource   112    0         7.710E-04   0.0        1.124         1.124         1        
0            1         AreaSource   104    0         8.090E-04   0.0        1.020         1.020         1        
2            1         AreaSource   104    0         7.341E-04   0.0        1.020         1.020         1        
1            6         AreaSource   103    0         7.939E-04   0.0        0.907         0.907         1        
3            6         AreaSource   103    0         6.762E-04   0.0        0.900         0.900         1        
1            3         AreaSource   87     0         7.081E-04   0.0        0.789         0.789         1        
3            3         AreaSource   87     0         7.100E-04   0.0        0.776         0.776         1        
3            9         AreaSource   62     0         6.900E-04   0.0        0.594         0.594         1        
1            9         AreaSource   62     0         6.900E-04   0.0        0.577         0.577         1        
3            5         AreaSource   58     0         6.702E-04   0.0        0.570         0.570         1        
1            5         AreaSource   58     0         6.731E-04   0.0        0.556         0.556         1        
1            7         AreaSource   42     0         7.422E-04   0.0        0.492         0.492         1        
3            7         AreaSource   42     0         6.449E-04   0.0        0.458         0.458         1        
3            4         AreaSource   32     0         6.540E-04   0.0        0.387         0.387         1        
1            8         AreaSource   36     0         7.319E-04   0.0        0.386         0.386         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.013       0.916      29            12            1,628     22    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
======================= ===== ====== ===== ===== =========
operation-duration      mean  stddev min   max   num_tasks
compute_gmfs_and_curves 0.009 0.003  0.004 0.012 13       
compute_ruptures        1.875 0.453  1.021 2.455 16       
======================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         30        0.691     16    
reading composite source model 0.911     0.0       1     
managing sources               0.587     0.0       1     
total compute_gmfs_and_curves  0.117     0.375     13    
compute poes                   0.090     0.0       13    
store source_info              0.045     0.0       1     
saving ruptures                0.016     0.0       16    
filtering sources              0.013     0.0       18    
make contexts                  0.012     0.0       13    
saving gmfs                    0.011     0.0       13    
filtering ruptures             0.003     0.0       14    
reading exposure               0.003     0.0       1     
aggregating hcurves            4.292E-05 0.0       13    
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======