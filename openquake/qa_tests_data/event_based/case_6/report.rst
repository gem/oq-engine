Event-based PSHA producing hazard curves only
=============================================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==================
calculation_mode             'event_based'     
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           50.0              
ses_per_logic_tree_path      300               
truncation_level             3.0               
rupture_mesh_spacing         2.0               
complex_fault_mesh_spacing   2.0               
width_of_mfd_bin             0.2               
area_source_discretization   20.0              
random_seed                  23                
master_seed                  0                 
concurrent_tasks             40                
============================ ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.600  `source_model1.xml <source_model1.xml>`_ simple(3)       3/3             
b12       0.400  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================= =========== ============================= =================
trt_id gsims                                                   distances   siteparams                    ruptparams       
====== ======================================================= =========== ============================= =================
0      BooreAtkinson2008 CampbellBozorgnia2008 ChiouYoungs2008 rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008 CampbellBozorgnia2008 ChiouYoungs2008 rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
====== ======================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=6, rlzs=6)
  0,BooreAtkinson2008: ['<0,b11,b11,w=0.3>']
  0,CampbellBozorgnia2008: ['<1,b11,b12,w=0.18>']
  0,ChiouYoungs2008: ['<2,b11,b13,w=0.12>']
  1,BooreAtkinson2008: ['<3,b12,b11,w=0.2>']
  1,CampbellBozorgnia2008: ['<4,b12,b12,w=0.12>']
  1,ChiouYoungs2008: ['<5,b12,b13,w=0.08>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      trt_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           2,144        61    
source_model2.xml 1      Active Shallow Crust 1           937          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   3,081
filtered_weight 122  
=============== =====

Informational data
------------------
====================================== ==================
compute_ruptures_max_received_per_task 87525             
compute_ruptures_sent.Monitor          175708            
compute_ruptures_sent.RlzsAssoc        364498            
compute_ruptures_sent.SiteCollection   27094             
compute_ruptures_sent.WeightedSequence 225668            
compute_ruptures_sent.int              310               
compute_ruptures_tot_received          3539670           
hazard.input_weight                    122.80000000000001
hazard.n_imts                          1                 
hazard.n_levels                        5.0               
hazard.n_realizations                  6                 
hazard.n_sites                         1                 
hazard.n_sources                       0                 
hazard.output_weight                   900.0             
====================================== ==================

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   61     307       0.001       0.051      4.101    
1            1         AreaSource   61     307       0.001       0.051      2.875    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  8.313     0.109     41    
total compute_ruptures         7.010     0.0       62    
compute poes                   5.490     0.0       3,081 
make contexts                  2.658     0.0       3,081 
filtering ruptures             1.421     0.0       3,081 
saving ruptures                0.916     0.0       1     
managing sources               0.307     0.0       1     
bulding hazard curves          0.112     0.0       41    
reading composite source model 0.106     0.0       1     
splitting sources              0.102     0.0       2     
aggregating hcurves            0.077     0.0       123   
aggregate curves               0.028     0.0       185   
store source_info              0.009     0.0       1     
filtering sources              0.002     0.0       2     
reading site collection        2.885E-05 0.0       1     
============================== ========= ========= ======