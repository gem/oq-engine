QA test for disaggregation case_2
=================================

num_sites = 2, sitecol = 730 B

Parameters
----------
============================ ==============
calculation_mode             disaggregation
number_of_logic_tree_samples 0             
maximum_distance             200.0         
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
============================ ==============

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
source_model_1 0.50   `source_model_1.xml <source_model_1.xml>`_ simple(2,1)     2/2             
source_model_2 0.50   `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2             
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

  <RlzsAssoc(5)
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
source_model_1.xml 0      Subduction IntraSlab 1           1815         45.375
source_model_1.xml 1      Active Shallow Crust 2           3630         90.75 
source_model_2.xml 2      Active Shallow Crust 1           1420         1420.0
================== ====== ==================== =========== ============ ======

=============== ========
#TRT models     3       
#sources        4       
#eff_ruptures   6865    
filtered_weight 1556.125
=============== ========

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 14       
Sent data                   139.33 KB
=========================== =========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
trt_model_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
2            1         SimpleFaultSource 1420.0 15        0.00295901  0.156149   0.0      
0            2         AreaSource        45.375 1         0.00120902  0.0        0.0      
1            1         AreaSource        45.375 1         0.00103998  0.0        0.0      
1            3         AreaSource        45.375 1         0.000962019 0.0        0.0      
============ ========= ================= ====== ========= =========== ========== =========