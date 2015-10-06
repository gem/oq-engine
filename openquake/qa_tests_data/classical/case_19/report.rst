SHARE OpenQuake Computational Settings
======================================

Parameters
----------
============================ =========
calculation_mode             classical
number_of_logic_tree_samples 0        
maximum_distance             200.0    
investigation_time           50.0     
ses_per_logic_tree_path      1        
truncation_level             3.0      
rupture_mesh_spacing         5.0      
complex_fault_mesh_spacing   5.0      
width_of_mfd_bin             0.2      
area_source_discretization   10.0     
random_seed                  23       
master_seed                  0        
concurrent_tasks             64       
============================ =========

Input files
-----------
======================= ==========================================================================
Name                    File                                                                      
======================= ==========================================================================
gsim_logic_tree         `complete_gmpe_logic_tree.xml <complete_gmpe_logic_tree.xml>`_            
job_ini                 `job.ini <job.ini>`_                                                      
source                  `simple_area_source_model.xml <simple_area_source_model.xml>`_            
source_model_logic_tree `simple_source_model_logic_tree.xml <simple_source_model_logic_tree.xml>`_
======================= ==========================================================================

Composite source model
----------------------
========= ====== ============================================================== ===================== ================ ===========
smlt_path weight source_model_file                                              gsim_logic_tree       num_realizations num_sources
========= ====== ============================================================== ===================== ================ ===========
b1        1.0    `simple_area_source_model.xml <simple_area_source_model.xml>`_ simple(0,4,0,0,0,0,0) 4/4              370        
========= ====== ============================================================== ===================== ================ ===========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(4)
  4,AtkinsonBoore2003SSlab: ['<0,b1,@_@_@_@_b51_@_@,w=0.2>']
  4,LinLee2008SSlab: ['<1,b1,@_@_@_@_b52_@_@,w=0.2>']
  4,YoungsEtAl1997SSlab: ['<2,b1,@_@_@_@_b53_@_@,w=0.2>']
  4,ZhaoEtAl2006SSlab: ['<3,b1,@_@_@_@_b54_@_@,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
=========== ====
#TRT models 5   
#sources    370 
#ruptures   7770
=========== ====

============================ ====== ==================== =========== ============
source_model                 trt_id trt                  num_sources num_ruptures
============================ ====== ==================== =========== ============
simple_area_source_model.xml 0      Subduction Interface 0           0           
simple_area_source_model.xml 1      Volcanic             0           0           
simple_area_source_model.xml 2      Shield               0           0           
simple_area_source_model.xml 3      Stable Shallow Crust 0           0           
simple_area_source_model.xml 4      Subduction Inslab    370         7770        
============================ ====== ==================== =========== ============

Expected data transfer for the sources
--------------------------------------
================================== =========
Number of tasks to generate        53       
Estimated sources to send          186.14 KB
Estimated hazard curves to receive 129 KB   
================================== =========