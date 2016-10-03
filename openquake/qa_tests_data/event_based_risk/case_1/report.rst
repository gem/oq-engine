Event Based Risk QA Test 1
==========================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54400.hdf5 Tue Sep 27 14:06:22 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
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
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           8            0.450 
================ ====== ==================== =========== ============ ======

Informational data
------------------
============================================= ============
compute_gmfs_and_curves_max_received_per_task 6,277       
compute_gmfs_and_curves_num_tasks             8           
compute_gmfs_and_curves_sent.eb_ruptures      15,696      
compute_gmfs_and_curves_sent.imts             560         
compute_gmfs_and_curves_sent.min_iml          1,224       
compute_gmfs_and_curves_sent.monitor          33,216      
compute_gmfs_and_curves_sent.rlzs_by_gsim     5,520       
compute_gmfs_and_curves_sent.sitecol          6,648       
compute_gmfs_and_curves_tot_received          47,307      
compute_ruptures_max_received_per_task        10,314      
compute_ruptures_num_tasks                    1           
compute_ruptures_sent.gsims                   164         
compute_ruptures_sent.monitor                 1,612       
compute_ruptures_sent.sitecol                 473         
compute_ruptures_sent.sources                 2,259       
compute_ruptures_tot_received                 10,314      
hazard.input_weight                           0.450       
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

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for src_group_id=0, contains 6 IMT(s), 2 realization(s)
and has a size of 1.22 KB / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 2 realization(s) x 4 loss type(s) x 1 losses x 8 bytes x 20 tasks = 5 KB

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
====== ========= ============ ====== ========= =========
grp_id source_id source_class weight calc_time num_sites
====== ========= ============ ====== ========= =========
0      2         PointSource  0.150  0.0       0        
0      1         PointSource  0.150  0.0       0        
0      3         PointSource  0.150  0.0       0        
====== ========= ============ ====== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
PointSource  0.0       3     
============ ========= ======

Information about the tasks
---------------------------
======================= ===== ====== ===== ===== =========
operation-duration      mean  stddev min   max   num_tasks
compute_ruptures        0.014 NaN    0.014 0.014 1        
compute_gmfs_and_curves 0.021 0.005  0.011 0.026 8        
======================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  0.171     0.016     8     
compute poes                   0.154     0.0       8     
total compute_ruptures         0.014     0.0       1     
make contexts                  0.009     0.0       8     
reading composite source model 0.005     0.0       1     
saving ruptures                0.004     0.0       1     
saving gmfs                    0.004     0.0       8     
reading exposure               0.003     0.0       1     
filtering ruptures             0.003     0.0       8     
managing sources               7.060E-04 0.0       1     
store source_info              4.351E-04 0.0       1     
reading site collection        3.099E-05 0.0       1     
aggregating hcurves            1.597E-05 0.0       8     
============================== ========= ========= ======