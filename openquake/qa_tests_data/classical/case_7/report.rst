Classical Hazard QA Test, Case 7
================================

gem-tstation:/home/michele/ssd/calc_45853.hdf5 updated Wed Aug 31 12:11:25 2016

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
width_of_mfd_bin             1.0                             
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
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ========================================== =============== ================
smlt_path weight source_model_file                          gsim_logic_tree num_realizations
========= ====== ========================================== =============== ================
b1        0.700  `source_model_1.xml <source_model_1.xml>`_ trivial(1)      1/1             
b2        0.300  `source_model_2.xml <source_model_2.xml>`_ trivial(1)      1/1             
========= ====== ========================================== =============== ================

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
  0,SadighEtAl1997(): ['<0,b1~b1,w=0.699999988079>']
  1,SadighEtAl1997(): ['<1,b2~b1,w=0.300000011921>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       grp_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust 2           1386         1,386 
source_model_2.xml 1      Active Shallow Crust 1           901          901   
================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        3    
#eff_ruptures   2,287
filtered_weight 2,287
=============== =====

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,137       
count_eff_ruptures_num_tasks             3           
count_eff_ruptures_sent.monitor          2,580       
count_eff_ruptures_sent.rlzs_by_gsim     1,548       
count_eff_ruptures_sent.sitecol          1,299       
count_eff_ruptures_sent.sources          3,360       
count_eff_ruptures_tot_received          3,411       
hazard.input_weight                      2,287       
hazard.n_imts                            1           
hazard.n_levels                          3.000       
hazard.n_realizations                    2           
hazard.n_sites                           1           
hazard.n_sources                         3           
hazard.output_weight                     6.000       
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class       weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ================== ====== ========= =========== ========== ============= ============= =========
0            2         ComplexFaultSource 485    1         0.0         6.073      0.0           0.0           0        
0            1         SimpleFaultSource  901    1         0.0         0.702      0.0           0.0           0        
1            1         SimpleFaultSource  901    1         0.0         0.674      0.0           0.0           0        
============ ========= ================== ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
================== =========== ========== ============= ============= ========= ======
source_class       filter_time split_time cum_calc_time max_calc_time num_tasks counts
================== =========== ========== ============= ============= ========= ======
ComplexFaultSource 0.0         6.073      0.0           0.0           0         1     
SimpleFaultSource  0.0         1.377      0.0           0.0           0         2     
================== =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 6.807     0.0       1     
managing sources               6.085     0.0       1     
total count_eff_ruptures       0.002     0.0       3     
aggregate curves               1.030E-04 0.0       3     
saving probability maps        3.910E-05 0.0       1     
reading site collection        3.695E-05 0.0       1     
store source_info              1.407E-05 0.0       1     
============================== ========= ========= ======