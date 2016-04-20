Classical Hazard QA Test, Case 2
================================

Datastore /home/michele/ssd/calc_11423.hdf5 last updated Wed Apr 20 09:37:27 2016 on gem-tstation

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
rupture_mesh_spacing         1.0                
complex_fault_mesh_spacing   1.0                
width_of_mfd_bin             0.001              
area_source_discretization   None               
random_seed                  1066               
master_seed                  0                  
sites_per_tile               1000               
oqlite_version               '0.13.0-git361357f'
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
source_model.xml 0      Active Shallow Crust 1           3,000        75    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2570          
count_eff_ruptures_num_tasks             1             
count_eff_ruptures_sent.monitor          2326          
count_eff_ruptures_sent.rlzs_assoc       2852          
count_eff_ruptures_sent.sitecol          437           
count_eff_ruptures_sent.siteidx          5             
count_eff_ruptures_sent.sources          1171          
count_eff_ruptures_tot_received          2570          
hazard.input_weight                      75.0          
hazard.n_imts                            1             
hazard.n_levels                          4.0           
hazard.n_realizations                    1             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     4.0           
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         PointSource  75     1         0.003       4.721E-05  0.0      
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.007     0.0       1     
managing sources               0.005     0.0       1     
store source_info              0.004     0.0       1     
filtering sources              0.003     0.0       1     
total count_eff_ruptures       2.410E-04 0.0       1     
splitting sources              4.721E-05 0.0       1     
reading site collection        3.099E-05 0.0       1     
aggregate curves               3.004E-05 0.0       1     
============================== ========= ========= ======