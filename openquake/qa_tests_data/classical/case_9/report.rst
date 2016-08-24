Classical Hazard QA Test, Case 9
================================

gem-tstation:/home/michele/ssd/calc_41999.hdf5 updated Wed Aug 24 08:03:46 2016

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
engine_version               '2.1.0-git46eb8e0'              
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
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
1      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

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
======================================== ============
count_eff_ruptures_max_received_per_task 1,198       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.monitor          1,736       
count_eff_ruptures_sent.rlzs_by_gsim     1,050       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          2,404       
count_eff_ruptures_tot_received          2,396       
hazard.input_weight                      162         
hazard.n_imts                            1           
hazard.n_levels                          4.000       
hazard.n_realizations                    2           
hazard.n_sites                           1           
hazard.n_sources                         2           
hazard.output_weight                     8.000       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
1            1         PointSource  87     1         0.004       1.216E-05  0.0           0.0           0        
0            1         PointSource  75     1         0.004       1.693E-05  0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.008       2.909E-05  0.0           0.0           0         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.013     0.0       1     
managing sources               0.012     0.0       1     
filtering sources              0.008     0.0       2     
store source_info              0.004     0.0       1     
total count_eff_ruptures       3.829E-04 0.0       2     
reading site collection        4.601E-05 0.0       1     
aggregate curves               2.909E-05 0.0       2     
splitting sources              2.909E-05 0.0       2     
saving probability maps        2.098E-05 0.0       1     
============================== ========= ========= ======