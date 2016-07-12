Event Based Risk QA Test 1
==========================

gem-tstation:/home/michele/ssd/calc_22583.hdf5 updated Tue May 31 15:37:27 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===============================
calculation_mode             'event_based_risk'             
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 100.0}
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
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

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
====================================== ============
event_based_risk_max_received_per_task 5,721       
event_based_risk_num_tasks             8           
event_based_risk_sent.assetcol         21,880      
event_based_risk_sent.monitor          21,040      
event_based_risk_sent.riskinput        26,034      
event_based_risk_sent.riskmodel        41,128      
event_based_risk_sent.rlzs_assoc       8,304       
event_based_risk_tot_received          44,570      
hostname                               gem-tstation
require_epsilons                       1           
====================================== ============

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
=========== =
#assets     4
#taxonomies 3
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
RC       1.000 NaN    1   1   1         1         
RM       1.000 0.0    1   1   2         2         
W        1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            2         PointSource  0.150  1         2.193E-05   0.0        0.003    
0            3         PointSource  0.150  1         1.788E-05   0.0        0.003    
0            1         PointSource  0.150  1         3.719E-05   0.0        0.003    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  7.701E-05   0.0        0.009     3     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.009 NaN    0.009 0.009 1        
compute_ruptures.memory_mb        0.0   NaN    0.0   0.0   1        
event_based_risk.time_sec         0.013 0.004  0.008 0.019 8        
event_based_risk.memory_mb        0.0   0.0    0.0   0.0   8        
compute_gmfs_and_curves.time_sec  0.008 0.003  0.005 0.011 8        
compute_gmfs_and_curves.memory_mb 0.0   0.0    0.0   0.0   8        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         0.106     0.0       8     
compute poes                   0.106     0.0       16    
total compute_gmfs_and_curves  0.065     0.0       8     
building hazard                0.063     0.0       8     
computing riskmodel            0.035     0.0       72    
building riskinputs            0.024     0.0       1     
saving event loss tables       0.017     0.0       8     
make contexts                  0.015     0.0       16    
total compute_ruptures         0.009     0.0       1     
aggregate losses               0.008     0.0       72    
saving gmfs                    0.007     0.0       16    
store source_info              0.006     0.0       1     
saving ruptures                0.006     0.0       1     
reading composite source model 0.006     0.0       1     
reading exposure               0.005     0.0       1     
filtering ruptures             0.002     0.0       8     
managing sources               0.002     0.0       1     
aggregate curves               7.269E-04 0.0       1     
filtering sources              7.701E-05 0.0       3     
reading site collection        3.099E-05 0.0       1     
============================== ========= ========= ======