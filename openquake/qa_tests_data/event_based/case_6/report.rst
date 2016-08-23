Event-based PSHA producing hazard curves only
=============================================

gem-tstation:/home/michele/ssd/calc_41622.hdf5 updated Tue Aug 23 17:47:52 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'event_based'                   
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      300                             
truncation_level             3.0                             
rupture_mesh_spacing         2.0                             
complex_fault_mesh_spacing   2.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   20.0                            
random_seed                  23                              
master_seed                  0                               
engine_version               '2.1.0-git5b04a6e'              
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
b11       0.600  `source_model1.xml <source_model1.xml>`_ simple(3)       3/3             
b12       0.400  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============================================================= =========== ============================= =================
grp_id gsims                                                         distances   siteparams                    ruptparams       
====== ============================================================= =========== ============================= =================
0      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008() CampbellBozorgnia2008() ChiouYoungs2008() rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
====== ============================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008(): ['<0,b11~b11,w=0.30000000298>']
  0,CampbellBozorgnia2008(): ['<1,b11~b12,w=0.180000001788>']
  0,ChiouYoungs2008(): ['<2,b11~b13,w=0.120000001192>']
  1,BooreAtkinson2008(): ['<3,b12~b11,w=0.19999999702>']
  1,CampbellBozorgnia2008(): ['<4,b12~b12,w=0.119999998212>']
  1,ChiouYoungs2008(): ['<5,b12~b13,w=0.0799999988079>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      grp_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           2144         61    
source_model2.xml 1      Active Shallow Crust 1           937          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   3,081
filtered_weight 122  
=============== =====

Informational data
------------------
====================================== ============
compute_ruptures_max_received_per_task 237,513     
compute_ruptures_num_tasks             20          
compute_ruptures_sent.monitor          17,520      
compute_ruptures_sent.rlzs_by_gsim     17,960      
compute_ruptures_sent.sitecol          8,660       
compute_ruptures_sent.sources          185,198     
compute_ruptures_tot_received          2,939,108   
hazard.input_weight                    122         
hazard.n_imts                          1           
hazard.n_levels                        5.000       
hazard.n_realizations                  6           
hazard.n_sites                         1           
hazard.n_sources                       2           
hazard.output_weight                   900         
hostname                               gem-tstation
====================================== ============

Specific information for event based
------------------------------------
======================== ======
Total number of ruptures 3,081 
Total number of events   16,186
Rupture multiplicity     5.253 
======================== ======

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            1         AreaSource   61     307       0.001       0.061      2.547         0.026         307      
1            1         AreaSource   61     307       0.001       0.065      1.619         0.018         307      
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.003       0.126      4.167         0.044         614       2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
========================== ===== ====== ===== ===== =========
measurement                mean  stddev min   max   num_tasks
compute_ruptures.time_sec  0.209 0.086  0.005 0.293 20       
compute_ruptures.memory_mb 0.0   0.0    0.0   0.0   20       
========================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_ruptures         4.177     0.0       20    
saving ruptures                2.262     0.0       1     
filtering ruptures             0.846     0.0       3,081 
managing sources               0.210     0.0       1     
splitting sources              0.126     0.0       2     
reading composite source model 0.121     0.0       1     
store source_info              0.010     0.0       1     
aggregate curves               0.007     0.0       20    
filtering sources              0.003     0.0       2     
reading site collection        3.290E-05 0.0       1     
============================== ========= ========= ======