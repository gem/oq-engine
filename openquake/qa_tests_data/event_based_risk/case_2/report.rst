Event Based Risk QA Test 2
==========================

gem-tstation:/home/michele/ssd/calc_16373.hdf5 updated Wed May 18 18:18:29 2016

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
oqlite_version               '0.13.0-git034c0a0'
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
====== ================= =========== ======================= =================
trt_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1,b1,w=1.0>']>

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
event_based_risk_max_received_per_task 4757          
event_based_risk_num_tasks             8             
event_based_risk_sent.assetcol         17680         
event_based_risk_sent.monitor          21680         
event_based_risk_sent.riskinput        25234         
event_based_risk_sent.riskmodel        15080         
event_based_risk_sent.rlzs_assoc       30160         
event_based_risk_tot_received          37165         
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
4 asset(s) x 1 realization(s) x 1 loss type(s) x 2 losses x 8 bytes x 20 tasks = 1.25 KB

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
0            2         PointSource  0.150  1         8.106E-05   0.0        0.004    
0            1         PointSource  0.150  1         1.168E-04   0.0        0.004    
0            3         PointSource  0.150  1         7.296E-05   0.0        0.004    
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  2.708E-04   0.0        0.012     3     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
================================= ===== ========= ===== ===== =========
measurement                       mean  stddev    min   max   num_tasks
compute_ruptures.time_sec         0.013 NaN       0.013 0.013 1        
compute_ruptures.memory_mb        0.301 NaN       0.301 0.301 1        
compute_gmfs_and_curves.time_sec  0.004 0.001     0.003 0.006 8        
compute_gmfs_and_curves.memory_mb 0.222 0.045     0.180 0.285 8        
event_based_risk.time_sec         0.007 8.947E-04 0.006 0.008 8        
event_based_risk.memory_mb        0.069 0.088     0.0   0.262 8        
================================= ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total event_based_risk         0.057     0.262     8     
compute poes                   0.047     0.0       16    
building hazard                0.036     0.0       8     
total compute_gmfs_and_curves  0.033     0.285     8     
make contexts                  0.015     0.0       16    
building riskinputs            0.014     0.0       1     
computing riskmodel            0.013     0.0       32    
total compute_ruptures         0.013     0.301     1     
store source_info              0.007     0.0       1     
saving ruptures                0.007     0.0       1     
reading exposure               0.007     0.0       1     
reading composite source model 0.006     0.0       1     
saving gmfs                    0.006     0.0       8     
saving event loss tables       0.005     0.0       8     
aggregate losses               0.004     0.0       32    
filtering ruptures             0.003     0.0       8     
managing sources               0.002     0.0       1     
aggregate curves               9.329E-04 0.0       1     
filtering sources              2.708E-04 0.0       3     
reading site collection        4.721E-05 0.0       1     
============================== ========= ========= ======