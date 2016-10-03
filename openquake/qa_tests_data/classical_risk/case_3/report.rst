Classical PSHA - Loss fractions QA test
=======================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54355.hdf5 Tue Sep 27 14:05:46 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
============================================== ========================

num_sites = 13, sitecol = 1.26 KB

Parameters
----------
============================ ================================
calculation_mode             'classical_risk'                
number_of_logic_tree_samples 1                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         5.0                             
complex_fault_mesh_spacing   5.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   10.0                            
random_seed                  23                              
master_seed                  0                               
avg_losses                   False                           
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
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
source_model.xml 0      Active Shallow Crust 14          25557        638   
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,355       
count_eff_ruptures_num_tasks             4           
count_eff_ruptures_sent.gsims            356         
count_eff_ruptures_sent.monitor          4,520       
count_eff_ruptures_sent.sitecol          2,692       
count_eff_ruptures_sent.sources          16,161      
count_eff_ruptures_tot_received          5,420       
hazard.input_weight                      845         
hazard.n_imts                            1           
hazard.n_levels                          19          
hazard.n_realizations                    1           
hazard.n_sites                           13          
hazard.n_sources                         15          
hazard.output_weight                     247         
hostname                                 gem-tstation
require_epsilons                         1           
======================================== ============

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   13        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
====== ========= ============ ====== ========= =========
grp_id source_id source_class weight calc_time num_sites
====== ========= ============ ====== ========= =========
0      135       AreaSource   82     0.0       0        
0      101       AreaSource   13     0.0       0        
0      225       AreaSource   13     0.0       0        
0      137       AreaSource   51     0.0       0        
0      253       AreaSource   76     0.0       0        
0      306       AreaSource   44     0.0       0        
0      59        AreaSource   18     0.0       0        
0      42        AreaSource   43     0.0       0        
0      8         AreaSource   120    0.0       0        
0      57        AreaSource   21     0.0       0        
0      359       AreaSource   57     0.0       0        
0      232       AreaSource   40     0.0       0        
0      27        AreaSource   37     0.0       0        
0      299       AreaSource   17     0.0       0        
====== ========= ============ ====== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       14    
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 2.507E-04 0.002 0.002 4        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.916     0.0       1     
managing sources               0.023     0.0       1     
total count_eff_ruptures       0.009     2.371     4     
reading exposure               0.006     0.0       1     
filter/split heavy sources     0.002     0.0       1     
store source_info              5.291E-04 0.0       1     
aggregate curves               6.175E-05 0.0       4     
saving probability maps        2.098E-05 0.0       1     
reading site collection        1.502E-05 0.0       1     
============================== ========= ========= ======