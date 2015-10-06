Classical PSHA with GMPE logic tree with multiple tectonic region types
=======================================================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         1.0      
complex_fault_mesh_spacing   1.0      
width_of_mfd_bin             0.1      
area_source_discretization   10.0     
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
============== ====== ========================================== =============== ================ ===========
smlt_path      weight source_model_file                          gsim_logic_tree num_realizations num_sources
============== ====== ========================================== =============== ================ ===========
SM1            0.50   `source_model_1.xml <source_model_1.xml>`_ complex(2,2)    4/4              2          
SM2_a3b1       0.250  `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2              16         
SM2_a3pt2b0pt8 0.250  `source_model_2.xml <source_model_2.xml>`_ simple(2,0)     2/2              16         
============== ====== ========================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(8)
  0,BooreAtkinson2008: ['<0,SM1,BA2008_C2003,w=0.125>', '<1,SM1,BA2008_T2002,w=0.125>']
  0,CampbellBozorgnia2008: ['<2,SM1,CB2008_C2003,w=0.125>', '<3,SM1,CB2008_T2002,w=0.125>']
  1,Campbell2003: ['<0,SM1,BA2008_C2003,w=0.125>', '<2,SM1,CB2008_C2003,w=0.125>']
  1,ToroEtAl2002: ['<1,SM1,BA2008_T2002,w=0.125>', '<3,SM1,CB2008_T2002,w=0.125>']
  2,BooreAtkinson2008: ['<4,SM2_a3b1,BA2008_@,w=0.125>']
  2,CampbellBozorgnia2008: ['<5,SM2_a3b1,CB2008_@,w=0.125>']
  3,BooreAtkinson2008: ['<6,SM2_a3pt2b0pt8,BA2008_@,w=0.125>']
  3,CampbellBozorgnia2008: ['<7,SM2_a3pt2b0pt8,CB2008_@,w=0.125>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== ===
#TRT models 4  
#sources    34 
#ruptures   510
=========== ===

================== ====== ======================== =========== ============
source_model       trt_id trt                      num_sources num_ruptures
================== ====== ======================== =========== ============
source_model_1.xml 0      Active Shallow Crust     1           15          
source_model_1.xml 1      Stable Continental Crust 1           15          
source_model_2.xml 2      Active Shallow Crust     16          240         
source_model_2.xml 3      Active Shallow Crust     16          240         
================== ====== ======================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== ========
Number of tasks to generate        18      
Estimated sources to send          44.85 KB
Estimated hazard curves to receive 13 KB   
================================== ========