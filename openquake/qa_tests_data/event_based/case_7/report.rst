Event-based PSHA with logic tree sampling
=========================================

============================================== ================================
gem-tstation:/home/michele/ssd/calc_48307.hdf5 updated Wed Sep  7 15:57:27 2016
engine_version                                 2.1.0-git3a14ca6                
hazardlib_version                              0.21.0-git89bccaf               
============================================== ================================

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 10                              
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      40                              
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   20.0                            
random_seed                  23                              
master_seed                  0                               
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.100  `source_model1.xml <source_model1.xml>`_ simple(3)       7/3             
b12       0.100  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008() CampbellBozorgnia2008()                   rjb rrup    z2pt5 vs30                    ztor mag rake dip
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008(): ['<3,b11~BA,w=0.1>', '<5,b11~BA,w=0.1>']
  0,CampbellBozorgnia2008(): ['<4,b11~CB,w=0.1>', '<6,b11~CB,w=0.1>']
  0,ChiouYoungs2008(): ['<0,b11~CY,w=0.1>', '<1,b11~CY,w=0.1>', '<2,b11~CY,w=0.1>']
  1,BooreAtkinson2008(): ['<8,b12~BA,w=0.1>', '<9,b12~BA,w=0.1>']
  1,CampbellBozorgnia2008(): ['<7,b12~CB,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      grp_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           2120         61    
source_model2.xml 1      Active Shallow Crust 1           478          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   2,598
filtered_weight 122  
=============== =====

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 238,714     
compute_ruptures_num_tasks             20          
compute_ruptures_sent.gsims            4,340       
compute_ruptures_sent.monitor          25,160      
compute_ruptures_sent.sitecol          9,460       
compute_ruptures_sent.sources          189,496     
compute_ruptures_tot_received          2,517,315   
hazard.input_weight                    614         
hazard.n_imts                          2           
hazard.n_levels                        38          
hazard.n_realizations                  10          
hazard.n_sites                         3           
hazard.n_sources                       2           
hazard.output_weight                   1,200       
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 2,598 
Total number of events   14,308
Rupture multiplicity     5.507 
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         AreaSource   61     307       0.0         0.118      2.341         0.025         307      
1            1         AreaSource   61     307       0.0         0.123      1.183         0.009         307      
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.0         0.242      3.524         0.034         614       2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
compute_ruptures   0.177 0.086  0.004 0.281 20       
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         3.547     0.0       20    
saving ruptures                1.259     0.0       20    
filtering ruptures             0.751     0.0       2,598 
managing sources               0.211     0.0       1     
reading composite source model 0.119     0.0       1     
store source_info              0.007     0.0       1     
reading site collection        4.387E-05 0.0       1     
============================== ========= ========= ======