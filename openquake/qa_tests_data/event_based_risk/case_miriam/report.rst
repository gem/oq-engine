Virtual Island - City C, 2 SES, grid=0.1
========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_48424.hdf5 Wed Sep  7 16:04:38 2016
engine_version                                 2.1.0-gitfaa2965        
hazardlib_version                              0.21.0-git89bccaf       
============================================== ========================

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
compute_ruptures_max_received_per_task 11,345      
compute_ruptures_num_tasks             16          
compute_ruptures_sent.gsims            1,424       
compute_ruptures_sent.monitor          21,057      
compute_ruptures_sent.sitecol          618,464     
compute_ruptures_sent.sources          1,033,433   
compute_ruptures_tot_received          113,660     
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
0            F         ComplexFaultSource 2,558  1,119     0.0         1.893      1.773         0.278         1,119    
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
ComplexFaultSource 0.0         1.893      1.773         0.278         1,119     1     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
======================= ===== ====== ===== ===== =========
operation-duration      mean  stddev min   max   num_tasks
compute_gmfs_and_curves 0.010 0.002  0.006 0.013 15       
compute_ruptures        0.114 0.124  0.005 0.279 16       
======================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               2.029     0.0       1     
total compute_ruptures         1.821     0.648     16    
saving gmfs                    1.777     0.0       15    
reading site collection        0.206     0.0       1     
total compute_gmfs_and_curves  0.154     0.0       15    
reading exposure               0.119     0.0       1     
compute poes                   0.101     0.0       44    
reading composite source model 0.070     0.0       1     
make contexts                  0.024     0.0       44    
filtering ruptures             0.018     0.0       57    
saving ruptures                0.016     0.0       16    
store source_info              0.014     0.0       1     
aggregating hcurves            3.505E-05 0.0       15    
============================== ========= ========= ======