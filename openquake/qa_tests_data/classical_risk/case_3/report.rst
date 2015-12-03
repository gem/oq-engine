Classical PSHA - Loss fractions QA test
=======================================

num_sites = 13

Parameters
----------
============================ ==============
calculation_mode             classical_risk
number_of_logic_tree_samples 1             
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
concurrent_tasks             16            
avg_losses                   False         
============================ ==============

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job.ini <job.ini>`_                                        
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.0    `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =============== =========== ======================= =================
trt_id gsims           distances   siteparams              ruptparams       
====== =============== =========== ======================= =================
0      ChiouYoungs2008 rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== =============== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============
source_model     trt_id trt                  num_sources num_ruptures
================ ====== ==================== =========== ============
source_model.xml 0      Active Shallow Crust 5101        66419       
================ ====== ==================== =========== ============

Exposure model
--------------
=========== ==
#assets     13
#taxonomies 4 
=========== ==

======== =======
Taxonomy #Assets
======== =======
A        4      
DS       2      
UFB      2      
W        5      
======== =======