Disaggregation calculation with Source Model containing an Area Source and a Simple Fault Source belonging to different tectonic region types
=============================================================================================================================================

Datastore /home/michele/ssd/calc_10525.hdf5 last updated Tue Apr 19 05:57:06 2016 on gem-tstation

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================
calculation_mode             'disaggregation'                                              
number_of_logic_tree_samples 0                                                             
maximum_distance             {'Stable Continental Crust': 150, 'Active Shallow Crust': 200}
investigation_time           50.0                                                          
ses_per_logic_tree_path      1                                                             
truncation_level             3.0                                                           
rupture_mesh_spacing         2.0                                                           
complex_fault_mesh_spacing   2.0                                                           
width_of_mfd_bin             0.1                                                           
area_source_discretization   5.0                                                           
random_seed                  23                                                            
master_seed                  0                                                             
oqlite_version               '0.13.0-git7c9cf8e'                                           
============================ ==============================================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b11       1.000  `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
1      ToroEtAl2002    rjb                                 mag              
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=1)
  0,ChiouYoungs2008: ['<0,b11,b11_b21,w=1.0>']
  1,ToroEtAl2002: ['<0,b11,b11_b21,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ======================== =========== ============ ======
source_model     trt_id trt                      num_sources eff_ruptures weight
================ ====== ======================== =========== ============ ======
source_model.xml 0      Active Shallow Crust     1           1,334        1,334 
source_model.xml 1      Stable Continental Crust 1           4,100        102   
================ ====== ======================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   5,434
filtered_weight 1,437
=============== =====

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 2471          
count_eff_ruptures_num_tasks             81            
count_eff_ruptures_sent.monitor          182574        
count_eff_ruptures_sent.rlzs_assoc       273375        
count_eff_ruptures_sent.sitecol          35397         
count_eff_ruptures_sent.siteidx          405           
count_eff_ruptures_sent.sources          5439173       
count_eff_ruptures_tot_received          200076        
hazard.input_weight                      1436.5        
hazard.n_imts                            1             
hazard.n_levels                          19.0          
hazard.n_realizations                    1             
hazard.n_sites                           1             
hazard.n_sources                         0             
hazard.output_weight                     19.0          
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            2         SimpleFaultSource 1,334  1,334     0.002       0.225      0.0      
1            1         AreaSource        102    205       7.899E-04   0.050      0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.503     0.0       1     
splitting sources              0.275     0.0       2     
reading composite source model 0.069     0.0       1     
total count_eff_ruptures       0.028     0.0       81    
store source_info              0.005     0.0       1     
filtering sources              0.002     0.0       2     
aggregate curves               0.001     0.0       81    
reading site collection        3.695E-05 0.0       1     
============================== ========= ========= ======