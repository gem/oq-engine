Classical Hazard QA Test, Case 8
================================

gem-tstation:/home/michele/ssd/calc_40710.hdf5 updated Mon Aug 22 12:51:08 2016

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
source                  `1.8 1.2 <1.8 1.2>`_                                        
source                  `2.0 1.0 <2.0 1.0>`_                                        
source                  `2.2 0.8 <2.2 0.8>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1_b2     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.300  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.400  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================== ============= ============= ==========
grp_id gsims                distances     siteparams    ruptparams
====== ==================== ============= ============= ==========
0      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
1      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
2      ['SadighEtAl1997()'] set(['rrup']) set(['vs30']) rake mag  
====== ==================== ============= ============= ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997(): ['<0,b1_b2~b1,w=0.30000000298>']
  1,SadighEtAl1997(): ['<1,b1_b3~b1,w=0.30000000298>']
  2,SadighEtAl1997(): ['<2,b1_b4~b1,w=0.39999999404>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3000         75    
source_model.xml 1      Active Shallow Crust 1           3000         75    
source_model.xml 2      Active Shallow Crust 1           3000         75    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        3    
#eff_ruptures   9,000
filtered_weight 225  
=============== =====

Informational data
------------------
=============================== ============
classical_max_received_per_task 1,820       
classical_num_tasks             3           
classical_sent.monitor          2,451       
classical_sent.rlzs_by_gsim     1,575       
classical_sent.sitecol          1,299       
classical_sent.sources          3,606       
classical_tot_received          5,460       
hazard.input_weight             225         
hazard.n_imts                   1           
hazard.n_levels                 4.000       
hazard.n_realizations           3           
hazard.n_sites                  1           
hazard.n_sources                3           
hazard.output_weight            12          
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
2            1         PointSource  75     1         0.004       1.502E-05  2.626         2.626         1        
1            1         PointSource  75     1         0.004       1.407E-05  2.558         2.558         1        
0            1         PointSource  75     1         0.004       2.003E-05  2.557         2.557         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.013       4.911E-05  7.741         7.741         3         3     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  2.581 0.040  2.557 2.627 3        
classical.memory_mb 0.0   0.0    0.0   0.0   3        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                7.742     0.0       3     
making contexts                3.707     0.0       9,000 
computing poes                 0.754     0.0       9,000 
managing sources               0.020     0.0       1     
reading composite source model 0.018     0.0       1     
filtering sources              0.013     0.0       3     
store source_info              0.011     0.0       1     
saving probability maps        0.006     0.0       1     
read poes                      0.002     0.0       1     
aggregate curves               9.084E-05 0.0       3     
splitting sources              4.911E-05 0.0       3     
reading site collection        3.409E-05 0.0       1     
============================== ========= ========= ======