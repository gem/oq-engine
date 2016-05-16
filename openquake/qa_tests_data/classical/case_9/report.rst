Classical Hazard QA Test, Case 9
================================

gem-tstation:/home/michele/ssd/calc_16343.hdf5 updated Mon May 16 14:19:48 2016

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           1.0                
ses_per_logic_tree_path      1                  
truncation_level             0.0                
rupture_mesh_spacing         0.01               
complex_fault_mesh_spacing   0.01               
width_of_mfd_bin             0.001              
area_source_discretization   10.0               
random_seed                  1066               
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git16c052c'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
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
====== ================ ========= ========== ==========
trt_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997(): ['<0,b1_b2,b1,w=0.5>']
  1,SadighEtAl1997(): ['<1,b1_b3,b1,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3,000        75    
source_model.xml 1      Active Shallow Crust 1           3,500        87    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   6,500
filtered_weight 162  
=============== =====

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2586          
count_eff_ruptures_num_tasks             2             
count_eff_ruptures_sent.monitor          4654          
count_eff_ruptures_sent.rlzs_assoc       6580          
count_eff_ruptures_sent.sitecol          874           
count_eff_ruptures_sent.siteidx          10            
count_eff_ruptures_sent.sources          2346          
count_eff_ruptures_tot_received          5172          
hazard.input_weight                      162.5         
hazard.n_imts                            1             
hazard.n_levels                          4.0           
hazard.n_realizations                    2             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     8.0           
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
1            1         PointSource  87     1         0.004       1.311E-05  0.0      
0            1         PointSource  75     1         0.004       1.502E-05  0.0      
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
PointSource  0.008       2.813E-05  0.0       2     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.035     0.0       1     
managing sources               0.011     0.0       1     
filtering sources              0.008     0.0       2     
store source_info              0.004     0.0       1     
total count_eff_ruptures       5.472E-04 0.0       2     
reading site collection        3.314E-05 0.0       1     
aggregate curves               3.290E-05 0.0       2     
splitting sources              2.813E-05 0.0       2     
============================== ========= ========= ======