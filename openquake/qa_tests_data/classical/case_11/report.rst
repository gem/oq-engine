Classical Hazard QA Test, Case 11
=================================

gem-tstation:/home/michele/ssd/calc_94.hdf5 updated Wed Apr 27 10:55:47 2016

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
b1_b2     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b3     0.600  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
b1_b4     0.200  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ============== ========= ========== ==========
trt_id gsims          distances siteparams ruptparams
====== ============== ========= ========== ==========
0      SadighEtAl1997 rrup      vs30       rake mag  
1      SadighEtAl1997 rrup      vs30       rake mag  
2      SadighEtAl1997 rrup      vs30       rake mag  
====== ============== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,SadighEtAl1997: ['<0,b1_b2,b1,w=0.2>']
  1,SadighEtAl1997: ['<1,b1_b3,b1,w=0.6>']
  2,SadighEtAl1997: ['<2,b1_b4,b1,w=0.2>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           3,500        87    
source_model.xml 1      Active Shallow Crust 1           3,000        75    
source_model.xml 2      Active Shallow Crust 1           2,500        62    
================ ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        3    
#eff_ruptures   9,000
filtered_weight 225  
=============== =====

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2594          
count_eff_ruptures_num_tasks             3             
count_eff_ruptures_sent.monitor          7029          
count_eff_ruptures_sent.rlzs_assoc       16035         
count_eff_ruptures_sent.sitecol          1311          
count_eff_ruptures_sent.siteidx          15            
count_eff_ruptures_sent.sources          3519          
count_eff_ruptures_tot_received          7782          
hazard.input_weight                      225.0         
hazard.n_imts                            1             
hazard.n_levels                          4.0           
hazard.n_realizations                    3             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     12.0          
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  87     1         0.007       2.694E-05  0.0      
1            1         PointSource  75     1         0.006       2.098E-05  0.0      
2            1         PointSource  62     1         0.005       2.003E-05  0.0      
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.031     0.0       1     
managing sources               0.025     0.0       1     
filtering sources              0.018     0.0       3     
store source_info              0.006     0.0       1     
total count_eff_ruptures       0.001     0.0       3     
aggregate curves               8.607E-05 0.0       3     
splitting sources              6.795E-05 0.0       3     
reading site collection        5.603E-05 0.0       1     
============================== ========= ========= ======