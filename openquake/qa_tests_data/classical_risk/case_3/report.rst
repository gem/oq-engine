Classical PSHA - Loss fractions QA test
=======================================

num_sites = 13, sitecol = 1.26 KB

Parameters
----------
============================ ===================
calculation_mode             'classical_risk'   
number_of_logic_tree_samples 1                  
maximum_distance             {'default': 200.0} 
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
sites_per_tile               1000               
oqlite_version               '0.13.0-gitcefd831'
============================ ===================

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
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
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

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008: ['<0,b1,b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     trt_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           1,613        53    
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== =================
classical_max_received_per_task 7563             
classical_sent.Monitor          6244             
classical_sent.RlzsAssoc        5720             
classical_sent.SiteCollection   1450             
classical_sent.WeightedSequence 3828             
classical_sent.int              10               
classical_tot_received          14291            
hazard.input_weight             845.7750000000001
hazard.n_imts                   1                
hazard.n_levels                 19.0             
hazard.n_realizations           1                
hazard.n_sites                  13               
hazard.n_sources                0                
hazard.output_weight            247.0            
=============================== =================

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

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            232       AreaSource   40     1         6.909E-04   0.0        2.271    
0            225       AreaSource   13     1         7.501E-04   0.0        0.328    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical_risk           6.346     1.277     13    
computing individual risk      6.325     0.0       13    
total classical                2.605     2.504     2     
making contexts                1.482     0.0       2,132 
reading composite source model 1.041     0.0       1     
computing poes                 0.487     0.0       1,613 
managing sources               0.040     0.0       1     
filtering sources              0.012     0.0       15    
store source_info              0.009     0.0       1     
reading exposure               0.006     0.0       1     
save curves_by_trt_gsim        0.003     0.0       1     
getting hazard                 0.002     0.0       13    
combine and save curves_by_rlz 0.001     0.0       1     
building riskinputs            0.001     0.0       1     
aggregate curves               8.578E-04 0.0       2     
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======