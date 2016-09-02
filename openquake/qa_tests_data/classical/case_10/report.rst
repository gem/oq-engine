Classical Hazard QA Test, Case 10
=================================

gem-tstation:/home/michele/ssd/calc_45840.hdf5 updated Wed Aug 31 12:10:40 2016

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
engine_version               '2.1.0-git49748af'              
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `0.0 <0.0>`_                                                
source                  `0.4 <0.4>`_                                                
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
source_model.xml 1      Active Shallow Crust 1           3000         75    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   6,000
filtered_weight 150  
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,145       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.monitor          1,736       
count_eff_ruptures_sent.rlzs_by_gsim     1,050       
count_eff_ruptures_sent.sitecol          866         
count_eff_ruptures_sent.sources          2,396       
count_eff_ruptures_tot_received          2,290       
hazard.input_weight                      150         
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
0            1         PointSource  75     1         0.0         2.501E-04  0.0           0.0           0        
1            1         PointSource  75     1         0.0         2.420E-04  0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
PointSource  0.0         4.921E-04  0.0           0.0           0         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.046     0.0       1     
reading composite source model 0.015     0.0       1     
total count_eff_ruptures       0.002     0.0       2     
aggregate curves               7.510E-05 0.0       2     
saving probability maps        4.411E-05 0.0       1     
reading site collection        3.481E-05 0.0       1     
store source_info              1.502E-05 0.0       1     
============================== ========= ========= ======