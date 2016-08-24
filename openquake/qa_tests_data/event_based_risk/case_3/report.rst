Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_41987.hdf5 updated Wed Aug 24 08:03:11 2016

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
engine_version               '2.1.0-git46eb8e0'                                              
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
compute_ruptures_tot_received          84,163      
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
0            0         AreaSource   610    543       0.001       0.140      7.113         0.052         543      
2            0         AreaSource   610    543       9.429E-04   0.135      6.520         0.014         543      
0            2         AreaSource   498    687       8.230E-04   0.127      2.253         0.016         262      
2            2         AreaSource   498    687       8.459E-04   0.126      2.236         0.009         262      
1            10        AreaSource   112    1         7.460E-04   0.0        1.239         1.239         1        
3            10        AreaSource   112    1         6.580E-04   0.0        1.149         1.149         1        
2            1         AreaSource   104    1         7.322E-04   0.0        1.028         1.028         1        
0            1         AreaSource   104    1         8.540E-04   0.0        1.011         1.011         1        
1            6         AreaSource   103    1         7.060E-04   0.0        0.929         0.929         1        
3            6         AreaSource   103    1         6.831E-04   0.0        0.909         0.909         1        
3            3         AreaSource   87     1         6.769E-04   0.0        0.856         0.856         1        
1            3         AreaSource   87     1         6.840E-04   0.0        0.776         0.776         1        
1            5         AreaSource   58     1         6.812E-04   0.0        0.642         0.642         1        
3            9         AreaSource   62     1         6.568E-04   0.0        0.608         0.608         1        
3            5         AreaSource   58     1         6.759E-04   0.0        0.580         0.580         1        
1            9         AreaSource   62     1         6.599E-04   0.0        0.577         0.577         1        
3            7         AreaSource   42     1         6.521E-04   0.0        0.486         0.486         1        
3            8         AreaSource   36     1         6.580E-04   0.0        0.477         0.477         1        
1            7         AreaSource   42     1         7.720E-04   0.0        0.470         0.470         1        
3            4         AreaSource   32     1         6.719E-04   0.0        0.395         0.395         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.016       0.528      30            12            1,628     22    
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         1.554 0.807  0.002 2.624 20       
compute_ruptures.memory_mb        0.032 0.115  0.0   0.504 20       
compute_gmfs_and_curves.time_sec  0.009 0.003  0.004 0.013 13       
compute_gmfs_and_curves.memory_mb 0.119 0.140  0.0   0.379 13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         31        0.504     20    
reading composite source model 0.885     0.0       1     
managing sources               0.721     0.0       1     
splitting sources              0.528     0.0       4     
total compute_gmfs_and_curves  0.115     0.379     13    
compute poes                   0.096     0.0       13    
store source_info              0.050     0.0       1     
saving gmfs                    0.028     0.0       44    
filtering sources              0.016     0.0       22    
saving ruptures                0.014     0.0       1     
make contexts                  0.013     0.0       13    
aggregate curves               0.007     0.0       20    
filtering ruptures             0.003     0.0       14    
reading exposure               0.003     0.0       1     
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======