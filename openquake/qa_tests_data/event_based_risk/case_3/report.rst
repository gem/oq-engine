Event Based Risk Lisbon
=======================

gem-tstation:/home/michele/ssd/calc_22578.hdf5 updated Tue May 31 15:37:09 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================
calculation_mode             'event_based_risk'                                            
number_of_logic_tree_samples 0                                                             
maximum_distance             {'Stable Shallow Crust': 400.0, 'Active Shallow Crust': 400.0}
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
engine_version               '2.0.0-git4fb4450'                                            
============================ ==============================================================

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
event_based_risk_max_received_per_task 4,523       
event_based_risk_num_tasks             13          
event_based_risk_sent.assetcol         21,398      
event_based_risk_sent.monitor          34,190      
event_based_risk_sent.riskinput        37,645      
event_based_risk_sent.riskmodel        26,728      
event_based_risk_sent.rlzs_assoc       22,932      
event_based_risk_tot_received          54,798      
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
=========== =
#assets     1
#taxonomies 1
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
M1_2_PC  1.000 NaN    1   1   1         1         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            0         AreaSource   610    543       0.001       0.185      6.419    
2            0         AreaSource   610    543       9.320E-04   0.147      6.260    
2            2         AreaSource   498    687       8.941E-04   0.137      2.091    
0            2         AreaSource   498    687       9.530E-04   0.136      2.042    
3            10        AreaSource   112    1         6.919E-04   0.0        1.427    
2            1         AreaSource   104    1         6.990E-04   0.0        1.308    
1            10        AreaSource   112    1         7.758E-04   0.0        1.001    
0            1         AreaSource   104    1         8.121E-04   0.0        0.955    
1            6         AreaSource   103    1         7.179E-04   0.0        0.909    
3            6         AreaSource   103    1         7.200E-04   0.0        0.900    
1            3         AreaSource   87     1         7.288E-04   0.0        0.833    
3            3         AreaSource   87     1         7.100E-04   0.0        0.763    
1            9         AreaSource   62     1         6.938E-04   0.0        0.682    
3            9         AreaSource   62     1         6.881E-04   0.0        0.609    
1            5         AreaSource   58     1         7.129E-04   0.0        0.552    
3            5         AreaSource   58     1         7.250E-04   0.0        0.511    
1            4         AreaSource   32     1         7.262E-04   0.0        0.427    
1            7         AreaSource   42     1         6.862E-04   0.0        0.371    
3            7         AreaSource   42     1         6.840E-04   0.0        0.368    
3            4         AreaSource   32     1         7.329E-04   0.0        0.333    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.017       0.606      29        22    
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.819 0.367  0.002 1.428 36       
compute_ruptures.memory_mb        0.017 0.105  0.0   0.629 36       
event_based_risk.time_sec         0.008 0.003  0.004 0.013 13       
event_based_risk.memory_mb        0.0   0.0    0.0   0.0   13       
compute_gmfs_and_curves.time_sec  0.007 0.002  0.003 0.011 13       
compute_gmfs_and_curves.memory_mb 0.234 0.371  0.0   0.824 13       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         29        0.629     36    
reading composite source model 0.980     0.0       1     
managing sources               0.728     0.0       1     
splitting sources              0.606     0.0       4     
compute poes                   0.145     0.0       26    
total event_based_risk         0.102     0.0       13    
building hazard                0.087     0.0       13    
total compute_gmfs_and_curves  0.085     0.824     13    
saving gmfs                    0.027     0.0       44    
store source_info              0.024     0.0       1     
building riskinputs            0.021     0.0       1     
make contexts                  0.018     0.0       26    
filtering sources              0.017     0.0       22    
saving ruptures                0.013     0.0       1     
computing riskmodel            0.007     0.0       13    
aggregate curves               0.007     0.0       36    
reading exposure               0.004     0.0       1     
filtering ruptures             0.004     0.0       14    
saving event loss tables       0.003     0.0       13    
aggregate losses               0.002     0.0       13    
reading site collection        9.060E-06 0.0       1     
============================== ========= ========= ======