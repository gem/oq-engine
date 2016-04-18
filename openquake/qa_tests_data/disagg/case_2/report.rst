QA test for disaggregation case_2
=================================

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ==================
calculation_mode             'disaggregation'  
number_of_logic_tree_samples 0                 
maximum_distance             {'default': 200.0}
investigation_time           1.0               
ses_per_logic_tree_path      1                 
truncation_level             3.0               
rupture_mesh_spacing         4.0               
complex_fault_mesh_spacing   4.0               
width_of_mfd_bin             0.1               
area_source_discretization   10.0              
random_seed                  23                
master_seed                  0                 
concurrent_tasks             10                
============================ ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model_1.xml <source_model_1.xml>`_                  
source                  `source_model_2.xml <source_model_2.xml>`_                  
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============== ====== ========================================== =============== ================
smlt_path      weight source_model_file                          gsim_logic_tree num_realizations
============== ====== ========================================== =============== ================
source_model_1 0.500  `source_model_1.xml <source_model_1.xml>`_ simple(2,1)     2/2             
source_model_2 0.500  `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2             
============== ====== ========================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================================= =========== ======================= =================
trt_id gsims                             distances   siteparams              ruptparams       
====== ================================= =========== ======================= =================
0      YoungsEtAl1997SSlab               rrup        vs30                    hypo_depth mag   
1      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
2      BooreAtkinson2008 ChiouYoungs2008 rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== ================================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=4)
  0,YoungsEtAl1997SSlab: ['<0,source_model_1,BooreAtkinson2008_YoungsEtAl1997SSlab,w=0.25>', '<1,source_model_1,ChiouYoungs2008_YoungsEtAl1997SSlab,w=0.25>']
  1,BooreAtkinson2008: ['<0,source_model_1,BooreAtkinson2008_YoungsEtAl1997SSlab,w=0.25>']
  1,ChiouYoungs2008: ['<1,source_model_1,ChiouYoungs2008_YoungsEtAl1997SSlab,w=0.25>']
  2,BooreAtkinson2008: ['<2,source_model_2,BooreAtkinson2008_@,w=0.25>']
  2,ChiouYoungs2008: ['<3,source_model_2,ChiouYoungs2008_@,w=0.25>']>

Number of ruptures per tectonic region type
-------------------------------------------
================== ====== ==================== =========== ============ ======
source_model       trt_id trt                  num_sources eff_ruptures weight
================== ====== ==================== =========== ============ ======
source_model_1.xml 0      Subduction Intraslab 1           1,815        45    
source_model_1.xml 1      Active Shallow Crust 2           3,630        90    
source_model_2.xml 2      Active Shallow Crust 1           1,420        1,420 
================== ====== ==================== =========== ============ ======

=============== =====
#TRT models     3    
#sources        4    
#eff_ruptures   6,865
filtered_weight 1,556
=============== =====

Informational data
------------------
======================================== ========
count_eff_ruptures_max_received_per_task 3159    
count_eff_ruptures_sent.Monitor          52506   
count_eff_ruptures_sent.RlzsAssoc        112914  
count_eff_ruptures_sent.SiteCollection   8298    
count_eff_ruptures_sent.WeightedSequence 21981   
count_eff_ruptures_sent.int              90      
count_eff_ruptures_tot_received          56847   
hazard.input_weight                      1556.125
hazard.n_imts                            1       
hazard.n_levels                          19.0    
hazard.n_realizations                    4       
hazard.n_sites                           2       
hazard.n_sources                         0       
hazard.output_weight                     152.0   
======================================== ========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
2            1         SimpleFaultSource 1,420  15        0.003       0.110      0.0      
1            1         AreaSource        45     1         7.811E-04   0.0        0.0      
0            2         AreaSource        45     1         7.510E-04   0.0        0.0      
1            3         AreaSource        45     1         6.840E-04   0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.140     0.0       1     
splitting sources              0.110     0.0       1     
reading composite source model 0.054     0.0       1     
total count_eff_ruptures       0.006     0.0       18    
filtering sources              0.005     0.0       4     
store source_info              0.003     0.0       1     
aggregate curves               2.358E-04 0.0       18    
reading site collection        2.909E-05 0.0       1     
============================== ========= ========= ======