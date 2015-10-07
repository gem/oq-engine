Disaggregation calculation with Source Model containing an Area Source and a Simple Fault Source belonging to different tectonic region types
=============================================================================================================================================

Parameters
----------
============================ ==============
calculation_mode             disaggregation
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
============================ ==============

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
========= ====== ====================================== =============== ================ ===========
smlt_path weight source_model_file                      gsim_logic_tree num_realizations num_sources
========= ====== ====================================== =============== ================ ===========
b11       1.00   `source_model.xml <source_model.xml>`_ trivial(1,1)    1/1              1539       
========= ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,ChiouYoungs2008: ['<0,b11,b11_b21,w=1.0>']
  1,ToroEtAl2002: ['<0,b11,b11_b21,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== ====
#TRT models 2   
#sources    1539
#ruptures   5434
=========== ====

================ ====== ======================== =========== ============
source_model     trt_id trt                      num_sources num_ruptures
================ ====== ======================== =========== ============
source_model.xml 0      Active Shallow Crust     1334        1334        
source_model.xml 1      Stable Continental Crust 205         4100        
================ ====== ======================== =========== ============