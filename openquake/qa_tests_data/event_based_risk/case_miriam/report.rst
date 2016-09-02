Virtual Island - City C, 2 SES, grid=0.1
========================================

gem-tstation:/home/michele/ssd/calc_45835.hdf5 updated Wed Aug 31 12:10:39 2016

num_sites = 281, sitecol = 37.75 KB

Parameters
----------
============================ ================================================================
calculation_mode             'event_based_risk'                                              
number_of_logic_tree_samples 0                                                               
maximum_distance             {u'Subduction Interface': 200.0, u'Active Shallow Crust': 200.0}
investigation_time           50.0                                                            
ses_per_logic_tree_path      2                                                               
truncation_level             4.0                                                             
rupture_mesh_spacing         10.0                                                            
complex_fault_mesh_spacing   10.0                                                            
width_of_mfd_bin             0.2                                                             
area_source_discretization   None                                                            
random_seed                  1024                                                            
master_seed                  100                                                             
avg_losses                   False                                                           
engine_version               '2.1.0-git49748af'                                              
============================ ================================================================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1,0)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= ========= ========== ==========
grp_id gsims             distances siteparams ruptparams
====== ================= ========= ========== ==========
0      AkkarBommer2010() rjb       vs30       rake mag  
====== ================= ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,AkkarBommer2010(): ['<0,b1~b1_@,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           44           2,558 
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 11,268      
compute_ruptures_num_tasks             16          
compute_ruptures_sent.monitor          20,432      
compute_ruptures_sent.rlzs_by_gsim     9,824       
compute_ruptures_sent.sitecol          618,464     
compute_ruptures_sent.sources          1,033,433   
compute_ruptures_tot_received          112,582     
hazard.input_weight                    2,558       
hazard.n_imts                          1           
hazard.n_levels                        50          
hazard.n_realizations                  1           
hazard.n_sites                         281         
hazard.n_sources                       1           
hazard.output_weight                   14,050      
hostname                               gem-tstation
require_epsilons                       1           
====================================== ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 44   
Total number of events   45   
Rupture multiplicity     1.023
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for src_group_id=0, contains 1 IMT(s), 1 realization(s)
and has a size of 49.39 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
548 asset(s) x 1 realization(s) x 1 loss type(s) x 1 losses x 8 bytes x 20 tasks = 85.62 KB

Exposure model
--------------
=============== ========
#assets         548     
#taxonomies     11      
deductibile     absolute
insurance_limit absolute
=============== ========

========== ===== ====== === === ========= ==========
taxonomy   mean  stddev min max num_sites num_assets
A-SPSB-1   1.250 0.463  1   2   8         10        
MC-RCSB-1  1.286 0.561  1   3   21        27        
MC-RLSB-2  1.256 0.880  1   6   39        49        
MR-RCSB-2  1.456 0.799  1   6   171       249       
MR-SLSB-1  1.000 0.0    1   1   5         5         
MS-FLSB-2  1.250 0.452  1   2   12        15        
MS-SLSB-1  1.545 0.934  1   4   11        17        
PCR-RCSM-5 1.000 0.0    1   1   2         2         
PCR-SLSB-1 1.000 0.0    1   1   3         3         
W-FLFB-2   1.222 0.502  1   3   54        66        
W-SLFB-1   1.265 0.520  1   3   83        105       
*ALL*      1.950 1.306  1   10  281       548       
========== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
0            F         ComplexFaultSource 2,558  1,119     0.0         2.105      1.863         0.282         1,119    
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
ComplexFaultSource 0.0         2.105      1.863         0.282         1,119     1     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.119 0.132  0.005 0.283 16       
compute_ruptures.memory_mb        0.047 0.101  0.0   0.266 16       
compute_gmfs_and_curves.time_sec  0.006 0.002  0.002 0.008 23       
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   23       
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ======== ========= ======
operation                      time_sec memory_mb counts
============================== ======== ========= ======
managing sources               2.248    0.0       1     
total compute_ruptures         1.910    0.266     16    
reading site collection        0.212    0.0       1     
total compute_gmfs_and_curves  0.137    0.0       23    
reading composite source model 0.114    0.0       1     
reading exposure               0.094    0.0       1     
compute poes                   0.087    0.0       44    
saving ruptures                0.036    0.0       1     
make contexts                  0.022    0.0       44    
store source_info              0.020    0.0       1     
saving gmfs                    0.015    0.0       23    
filtering ruptures             0.013    0.0       57    
aggregate curves               0.007    0.0       16    
============================== ======== ========= ======