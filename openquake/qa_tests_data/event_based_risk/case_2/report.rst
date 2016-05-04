Event Based Risk QA Test 2
==========================

gem-tstation:/home/michele/ssd/calc_12611.hdf5 updated Wed May  4 04:54:08 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'event_based_risk' 
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 100.0} 
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
oqlite_version               '0.13.0-git02c4b55'
============================ ===================

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
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 3           8            0.450 
================ ====== ==================== =========== ============ ======

Informational data
------------------
====================================== ==============
event_based_risk_max_received_per_task 4764          
event_based_risk_num_tasks             8             
event_based_risk_sent.assetcol         17680         
event_based_risk_sent.monitor          21680         
event_based_risk_sent.riskinput        24698         
event_based_risk_sent.riskmodel        15080         
event_based_risk_sent.rlzs_assoc       20984         
event_based_risk_tot_received          37092         
hostname                               'gem-tstation'
require_epsilons                       True          
====================================== ==============

Specific information for event based
------------------------------------
======================== =====
Total number of ruptures 8    
Total number of events   26   
Rupture multiplicity     3.250
======================== =====

Maximum memory allocated for the GMFs
-------------------------------------
The largest GMF block is for trt_model_id=0, contains 3 IMT(s), 1 realization(s)
and has a size of 312 B / num_tasks

Estimated data transfer for the avglosses
-----------------------------------------
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 40 tasks = 2.5 KB

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
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  0.150  1         1.810E-04   0.0        0.020    
0            2         PointSource  0.150  1         1.380E-04   0.0        0.005    
0            3         PointSource  0.150  1         1.268E-04   0.0        0.005    
============ ========= ============ ====== ========= =========== ========== =========

Information about the tasks
---------------------------
================================= ===== ====== ===== ===== =========
measurement                       mean  stddev min   max   num_tasks
compute_ruptures.time_sec         0.030 NaN    0.030 0.030 1        
compute_ruptures.memory_mb        0.219 NaN    0.219 0.219 1        
compute_gmfs_and_curves.time_sec  0.005 0.001  0.004 0.007 8        
compute_gmfs_and_curves.memory_mb 0.181 0.024  0.164 0.238 8        
event_based_risk.time_sec         0.010 0.002  0.006 0.013 8        
event_based_risk.memory_mb        0.400 0.161  0.168 0.523 8        
================================= ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         0.079     0.523     8     
compute poes                   0.045     0.0       16    
total compute_gmfs_and_curves  0.042     0.238     8     
building hazard                0.040     0.0       8     
total compute_ruptures         0.030     0.219     1     
make contexts                  0.028     0.0       16    
computing riskmodel            0.026     0.0       32    
reading exposure               0.009     0.0       1     
store source_info              0.009     0.0       1     
reading composite source model 0.008     0.0       1     
saving ruptures                0.007     0.0       1     
aggregate losses               0.006     0.0       32    
saving event loss tables       0.004     0.0       8     
saving gmfs                    0.004     0.0       8     
filtering ruptures             0.003     0.0       8     
managing sources               0.003     0.0       1     
aggregate curves               9.599E-04 0.0       1     
filtering sources              4.458E-04 0.0       3     
reading site collection        5.889E-05 0.0       1     
============================== ========= ========= ======