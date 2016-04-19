Classical Hazard QA Test, Case 7
================================

Datastore /home/michele/ssd/calc_10554.hdf5 last updated Tue Apr 19 05:58:16 2016 on gem-tstation

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
width_of_mfd_bin             1.0                
area_source_discretization   10.0               
random_seed                  1066               
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

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
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,SadighEtAl1997: ['<0,b1,b1,w=0.7>']
  1,SadighEtAl1997: ['<1,b2,b1,w=0.3>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       trt_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Active Shallow Crust 2           1,386        1,386 
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
======================================== ==============
count_eff_ruptures_max_received_per_task 2656          
count_eff_ruptures_num_tasks             3             
count_eff_ruptures_sent.monitor          7236          
count_eff_ruptures_sent.rlzs_assoc       12690         
count_eff_ruptures_sent.sitecol          1311          
count_eff_ruptures_sent.siteidx          15            
count_eff_ruptures_sent.sources          3342          
count_eff_ruptures_tot_received          7968          
hazard.input_weight                      2287.0        
hazard.n_imts                            1             
hazard.n_levels                          3.0           
hazard.n_realizations                    2             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     6.0           
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            2         ComplexFaultSource 485    1         0.002       7.946      0.0      
0            1         SimpleFaultSource  901    1         0.001       0.534      0.0      
1            1         SimpleFaultSource  901    1         0.001       0.501      0.0      
============ ========= ================== ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 9.154     0.0       1     
managing sources               8.990     0.0       1     
splitting sources              8.981     0.0       3     
filtering sources              0.004     0.0       3     
store source_info              0.004     0.0       1     
total count_eff_ruptures       0.001     0.0       3     
aggregate curves               6.104E-05 0.0       3     
reading site collection        3.815E-05 0.0       1     
============================== ========= ========= ======