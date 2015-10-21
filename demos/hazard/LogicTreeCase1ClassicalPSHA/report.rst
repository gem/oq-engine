Classical PSHA with non-trivial logic tree (2 source models and 2 GMPEs per tectonic region type)
=================================================================================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         2.0      
complex_fault_mesh_spacing   2.0      
width_of_mfd_bin             0.1      
area_source_discretization   5.0      
random_seed                  23       
master_seed                  0        
concurrent_tasks             64       
============================ =========

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
========= ====== ========================================== =============== ================ ===========
smlt_path weight source_model_file                          gsim_logic_tree num_realizations num_sources
========= ====== ========================================== =============== ================ ===========
b1        0.50   `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4              1539       
b2        0.50   `source_model_2.xml <source_model_2.xml>`_ complex(2,2)    4/4              1593       
========= ====== ========================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(8)
  0,BooreAtkinson2008: ['<0,b1,b11_b21,w=0.125>', '<1,b1,b11_b22,w=0.125>']
  0,ChiouYoungs2008: ['<2,b1,b12_b21,w=0.125>', '<3,b1,b12_b22,w=0.125>']
  1,Campbell2003: ['<1,b1,b11_b22,w=0.125>', '<3,b1,b12_b22,w=0.125>']
  1,ToroEtAl2002: ['<0,b1,b11_b21,w=0.125>', '<2,b1,b12_b21,w=0.125>']
  2,BooreAtkinson2008: ['<4,b2,b11_b21,w=0.125>', '<5,b2,b11_b22,w=0.125>']
  2,ChiouYoungs2008: ['<6,b2,b12_b21,w=0.125>', '<7,b2,b12_b22,w=0.125>']
  3,Campbell2003: ['<5,b2,b11_b22,w=0.125>', '<7,b2,b12_b22,w=0.125>']
  3,ToroEtAl2002: ['<4,b2,b11_b21,w=0.125>', '<6,b2,b12_b21,w=0.125>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== =====
#TRT models 4    
#sources    3132 
#ruptures   12651
=========== =====

================== ====== ======================== =========== ============
source_model       trt_id trt                      num_sources num_ruptures
================== ====== ======================== =========== ============
source_model_1.xml 0      Active Shallow Crust     1334        1334        
source_model_1.xml 1      Stable Continental Crust 205         4100        
source_model_2.xml 2      Active Shallow Crust     1297        1297        
source_model_2.xml 3      Stable Continental Crust 296         5920        
================== ====== ======================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =======
Number of tasks to generate        65     
Estimated sources to send          10.2 MB
Estimated hazard curves to receive 19 KB  
================================== =======