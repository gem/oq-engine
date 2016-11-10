Event Based Risk QA Test 1
==========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66973.hdf5 Wed Nov  9 08:14:37 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ================================
calculation_mode             'event_based_risk'              
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 100.0}
investigation_time           50.0                            
ses_per_logic_tree_path      20                              
truncation_level             3.0                             
rupture_mesh_spacing         5.0                             
complex_fault_mesh_spacing   5.0                             
width_of_mfd_bin             0.3                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  42                              
avg_losses                   True                            
============================ ================================

Input files
-----------
=========================== ========================================================================
Name                        File                                                                    
=========================== ========================================================================
contents_vulnerability      `vulnerability_model_coco.xml <vulnerability_model_coco.xml>`_          
exposure                    `exposure.xml <exposure.xml>`_                                          
gsim_logic_tree             `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                            
job_ini                     `job.ini <job.ini>`_                                                    
nonstructural_vulnerability `vulnerability_model_nonstco.xml <vulnerability_model_nonstco.xml>`_    
occupants_vulnerability     `vulnerability_model_occupants.xml <vulnerability_model_occupants.xml>`_
source                      `source_model.xml <source_model.xml>`_                                  
source_model_logic_tree     `source_model_logic_tree.xml <source_model_logic_tree.xml>`_            
structural_vulnerability    `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_          
=========================== ========================================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): ['<1,b1~b2,w=0.5>']
  0,ChiouYoungs2008(): ['<0,b1~b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 3           8            18          
================ ====== ==================== =========== ============ ============

Informational data
------------------
============================================= ============
compute_gmfs_and_curves_max_received_per_task 5,949       
compute_gmfs_and_curves_num_tasks             8           
compute_gmfs_and_curves_sent.getter           31,488      
compute_gmfs_and_curves_sent.monitor          33,136      
compute_gmfs_and_curves_sent.rlzs             4,664       
compute_gmfs_and_curves_tot_received          44,136      
compute_ruptures_max_received_per_task        11,731      
compute_ruptures_num_tasks                    1           
compute_ruptures_sent.gsims                   164         
compute_ruptures_sent.monitor                 1,609       
compute_ruptures_sent.sitecol                 473         
compute_ruptures_sent.sources                 2,259       
compute_ruptures_tot_received                 11,731      
hazard.input_weight                           1.800       
hazard.n_imts                                 6           
hazard.n_levels                               34          
hazard.n_realizations                         2           
hazard.n_sites                                3           
hazard.n_sources                              3           
hazard.output_weight                          204         
hostname                                      gem-tstation
require_epsilons                              1           
============================================= ============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 8    
Total number of events   26   
Rupture multiplicity     3.250
======================== =====

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 4 loss type(s) x 1 losses x 8 bytes x 50 tasks = 12.5 KB

Exposure model
--------------
=============== ========
#assets         4       
#taxonomies     3       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC       1.000 NaN    1   1   1         1         
RM       1.000 0.0    1   1   2         2         
W        1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
0      2         PointSource  6            0.0       1         0        
0      1         PointSource  6            0.0       1         0        
0      3         PointSource  6            0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.017 NaN    0.017 0.017 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
total compute_gmfs_and_curves    0.190     0.621     8     
total compute_ruptures           0.017     0.0       1     
saving gmfs                      0.010     0.0       8     
reading composite source model   0.007     0.0       1     
filtering composite source model 0.004     0.0       1     
reading exposure                 0.004     0.0       1     
filtering ruptures               0.004     0.0       8     
saving ruptures                  0.003     0.0       1     
managing sources                 0.003     0.0       1     
store source_info                8.430E-04 0.0       1     
reading site collection          4.196E-05 0.0       1     
aggregating hcurves              2.193E-05 0.0       8     
================================ ========= ========= ======