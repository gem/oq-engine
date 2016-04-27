Classical Hazard QA Test, Case 6
================================

gem-tstation:/home/michele/ssd/calc_85.hdf5 updated Wed Apr 27 10:55:25 2016

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
oqlite_version               '0.13.0-gitcbbc4a8'
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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           1,386        1,386 
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2557          
count_eff_ruptures_num_tasks             2             
count_eff_ruptures_sent.monitor          4612          
count_eff_ruptures_sent.rlzs_assoc       5248          
count_eff_ruptures_sent.sitecol          874           
count_eff_ruptures_sent.siteidx          10            
count_eff_ruptures_sent.sources          2256          
count_eff_ruptures_tot_received          5114          
hazard.input_weight                      1386.0        
hazard.n_imts                            1             
hazard.n_levels                          3.0           
hazard.n_realizations                    1             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     3.0           
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ================== ====== ========= =========== ========== =========
trt_model_id source_id source_class       weight split_num filter_time split_time calc_time
============ ========= ================== ====== ========= =========== ========== =========
0            2         ComplexFaultSource 485    1         0.001       8.023      0.0      
0            1         SimpleFaultSource  901    1         0.001       0.501      0.0      
============ ========= ================== ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 8.650     0.0       1     
managing sources               8.530     0.0       1     
splitting sources              8.524     0.0       2     
store source_info              0.004     0.0       1     
filtering sources              0.003     0.0       2     
total count_eff_ruptures       7.417E-04 0.0       2     
reading site collection        3.600E-05 0.0       1     
aggregate curves               3.409E-05 0.0       2     
============================== ========= ========= ======