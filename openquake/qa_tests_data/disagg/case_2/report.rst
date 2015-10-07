QA test for disaggregation case_2
=================================

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
concurrent_tasks             64            
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
============== ====== ========================================== =============== ================ ===========
smlt_path      weight source_model_file                          gsim_logic_tree num_realizations num_sources
============== ====== ========================================== =============== ================ ===========
source_model_1 0.50   `source_model_1.xml <source_model_1.xml>`_ simple(2,1)     2/2              363        
source_model_2 0.50   `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2              15         
============== ====== ========================================== =============== ================ ===========

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
=========== ====
#TRT models 3   
#sources    378 
#ruptures   6865
=========== ====

================== ====== ==================== =========== ============
source_model       trt_id trt                  num_sources num_ruptures
================== ====== ==================== =========== ============
source_model_1.xml 0      Subduction IntraSlab 121         1815        
source_model_1.xml 1      Active Shallow Crust 242         3630        
source_model_2.xml 2      Active Shallow Crust 15          1420        
================== ====== ==================== =========== ============