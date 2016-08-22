Classical Hazard QA Test, Case 9
================================

gem-tstation:/home/michele/ssd/calc_40706.hdf5 updated Mon Aug 22 12:50:50 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'active shallow crust': 200.0}
investigation_time           1.0                             
ses_per_logic_tree_path      1                               
truncation_level             0.0                             
rupture_mesh_spacing         0.01                            
complex_fault_mesh_spacing   0.01                            
width_of_mfd_bin             0.001                           
area_source_discretization   10.0                            
random_seed                  1066                            
master_seed                  0                               
sites_per_tile               10000                           
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `7.0 <7.0>`_                                                
source                  `7.5 <7.5>`_                                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.500  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
1      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.5>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3000         75    
source_model.xml 1      Active Shallow Crust 1           3500         87    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   6,500
filtered_weight 162  
=============== =====

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,823       
classical_num_tasks             2           
classical_sent.monitor          1,634       
classical_sent.rlzs_by_gsim     1,050       
classical_sent.sitecol          866         
classical_sent.sources          2,404       
classical_tot_received          3,643       
hazard.input_weight             162         
hazard.n_imts                   1           
hazard.n_levels                 4.000       
hazard.n_realizations           2           
hazard.n_sites                  1           
hazard.n_sources                2           
hazard.output_weight            8.000       
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
1            1         PointSource  87     1         0.005       1.383E-05  2.923         2.923         1        
0            1         PointSource  75     1         0.004       1.812E-05  2.578         2.578         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.009       3.195E-05  5.501         5.501         2         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  2.751 0.244  2.579 2.923 2        
classical.memory_mb 0.781 1.105  0.0   1.562 2        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                5.502     1.562     2     
making contexts                2.618     0.0       6,500 
computing poes                 0.532     0.0       6,500 
reading composite source model 0.015     0.0       1     
managing sources               0.013     0.0       1     
store source_info              0.011     0.0       1     
filtering sources              0.009     0.0       2     
saving probability maps        0.004     0.0       1     
read poes                      0.002     0.0       1     
aggregate curves               6.700E-05 0.0       2     
reading site collection        3.314E-05 0.0       1     
splitting sources              3.195E-05 0.0       2     
============================== ========= ========= ======