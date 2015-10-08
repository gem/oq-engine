Classical PSHA QA test with sites_csv
=====================================

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
sites                   `qa_sites.csv <qa_sites.csv>`_                              
source                  `simple_fault.xml <simple_fault.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
============ ====== ====================================== =============== ================ ===========
smlt_path    weight source_model_file                      gsim_logic_tree num_realizations num_sources
============ ====== ====================================== =============== ================ ===========
simple_fault 1.00   `simple_fault.xml <simple_fault.xml>`_ simple(2)       2/2              15         
============ ====== ====================================== =============== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(2)
  0,AbrahamsonSilva2008: ['<0,simple_fault,AbrahamsonSilva2008,w=0.5>']
  0,CampbellBozorgnia2008: ['<1,simple_fault,CampbellBozorgnia2008,w=0.5>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
simple_fault.xml 0      Active Shallow Crust 15          447         
================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== ========
Number of tasks to generate        15      
Estimated sources to send          31.48 KB
Estimated hazard curves to receive 30 KB   
================================== ========