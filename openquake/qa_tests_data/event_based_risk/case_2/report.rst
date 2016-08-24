Event Based Risk QA Test 2
==========================

gem-tstation:/home/michele/ssd/calc_41985.hdf5 updated Wed Aug 24 08:03:05 2016

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
engine_version               '2.1.0-git46eb8e0'              
============================ ================================

Input files
-----------
======================== ==============================================================
Name                     File                                                          
======================== ==============================================================
exposure                 `exposure.xml <exposure.xml>`_                                
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                  
job_ini                  `job.ini <job.ini>`_                                          
source                   `source_model.xml <source_model.xml>`_                        
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_  
structural_vulnerability `vulnerability_model_stco.xml <vulnerability_model_stco.xml>`_
======================== ==============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

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
compute_ruptures_max_received_per_task 9,760       
compute_ruptures_num_tasks             1           
compute_ruptures_sent.monitor          1,094       
compute_ruptures_sent.rlzs_by_gsim     520         
compute_ruptures_sent.sitecol          473         
compute_ruptures_sent.sources          2,239       
compute_ruptures_tot_received          9,760       
hazard.input_weight                    0.450       
hazard.n_imts                          3           
hazard.n_levels                        5.000       
hazard.n_realizations                  1           
hazard.n_sites                         3           
hazard.n_sources                       3           
hazard.output_weight                   45          
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
The largest GMF block is for src_group_id=0, contains 3 IMT(s), 1 realization(s)
and has a size of 312 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 20 tasks = 1.25 KB

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
RC+      1.000 NaN    1   1   1         1         
RM       1.000 0.0    1   1   2         2         
W        1.000 NaN    1   1   1         1         
*ALL*    1.333 0.577  1   2   3         4         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            2         PointSource  0.150  1         2.098E-05   0.0        0.006         0.006         1        
0            3         PointSource  0.150  1         1.812E-05   0.0        0.006         0.006         1        
0            1         PointSource  0.150  1         3.505E-05   0.0        0.006         0.006         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  7.415E-05   0.0        0.018         0.018         3         3     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.019 NaN    0.019 0.019 1        
compute_ruptures.memory_mb        0.0   NaN    0.0   0.0   1        
compute_gmfs_and_curves.time_sec  0.006 0.001  0.003 0.007 8        
compute_gmfs_and_curves.memory_mb 0.309 0.025  0.285 0.348 8        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  0.046     0.348     8     
compute poes                   0.030     0.0       8     
total compute_ruptures         0.019     0.0       1     
make contexts                  0.012     0.0       8     
saving ruptures                0.006     0.0       1     
store source_info              0.005     0.0       1     
reading composite source model 0.005     0.0       1     
filtering ruptures             0.004     0.0       8     
saving gmfs                    0.004     0.0       8     
reading exposure               0.003     0.0       1     
managing sources               0.003     0.0       1     
aggregate curves               7.200E-04 0.0       1     
filtering sources              7.415E-05 0.0       3     
reading site collection        3.910E-05 0.0       1     
============================== ========= ========= ======