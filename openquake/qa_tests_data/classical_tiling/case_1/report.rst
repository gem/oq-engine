Classical PSHA using Area Source
================================

Datastore /home/michele/ssd/calc_11468.hdf5 last updated Wed Apr 20 09:39:34 2016 on gem-tstation

num_sites = 6, sitecol = 969 B

Parameters
----------
============================ ===================
calculation_mode             'classical'        
number_of_logic_tree_samples 0                  
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      1                  
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.2                
area_source_discretization   5.0                
random_seed                  23                 
master_seed                  0                  
sites_per_tile               1                  
oqlite_version               '0.13.0-git361357f'
============================ ===================

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
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,BooreAtkinson2008: ['<0,b1,b1,w=0.6>']
  0,ChiouYoungs2008: ['<1,b1,b2,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1,640        41    
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ==============
count_eff_ruptures_max_received_per_task 3503          
count_eff_ruptures_num_tasks             12            
count_eff_ruptures_sent.monitor          39108         
count_eff_ruptures_sent.rlzs_assoc       38748         
count_eff_ruptures_sent.sitecol          5244          
count_eff_ruptures_sent.siteidx          60            
count_eff_ruptures_sent.sources          258192        
count_eff_ruptures_tot_received          42036         
hazard.input_weight                      41.0          
hazard.n_imts                            3             
hazard.n_levels                          19.0          
hazard.n_realizations                    2             
hazard.n_sites                           6             
hazard.n_sources                         0             
hazard.output_weight                     684.0         
hostname                                 'gem-tstation'
======================================== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   41     205       0.006       0.045      0.0      
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.086     0.0       1     
reading composite source model 0.046     0.0       1     
splitting sources              0.045     0.0       1     
filtering sources              0.006     0.0       6     
total count_eff_ruptures       0.005     0.0       12    
store source_info              0.004     0.0       1     
reading site collection        0.003     0.0       1     
aggregate curves               1.626E-04 0.0       12    
============================== ========= ========= ======