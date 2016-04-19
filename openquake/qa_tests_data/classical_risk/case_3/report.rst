Classical PSHA - Loss fractions QA test
=======================================

Datastore /home/michele/ssd/calc_10482.hdf5 last updated Tue Apr 19 05:56:31 2016 on gem-tstation

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
avg_losses                   False              
sites_per_tile               1000               
oqlite_version               '0.13.0-git7c9cf8e'
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
==================================== ==============
classical_risk_max_received_per_task 7388          
classical_risk_num_tasks             13            
classical_risk_sent.monitor          53924         
classical_risk_sent.riskinputs       14193         
classical_risk_sent.riskmodel        166556        
classical_risk_sent.rlzs_assoc       37011         
classical_risk_tot_received          96044         
hostname                             'gem-tstation'
==================================== ==============

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
0            232       AreaSource   40     1         6.940E-04   0.0        2.323    
0            225       AreaSource   13     1         7.110E-04   0.0        0.522    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical_risk           8.503     1.199     13    
computing individual risk      8.481     0.0       13    
total classical                2.856     2.637     2     
making contexts                1.583     0.0       2,132 
reading composite source model 1.078     0.0       1     
computing poes                 0.492     0.0       1,613 
managing sources               0.041     0.0       1     
filtering sources              0.012     0.0       15    
store source_info              0.011     0.0       1     
reading exposure               0.006     0.0       1     
save curves_by_trt_gsim        0.002     0.0       1     
getting hazard                 0.002     0.0       13    
combine and save curves_by_rlz 0.001     0.0       1     
building riskinputs            0.001     0.0       1     
aggregate curves               9.508E-04 0.0       2     
reading site collection        7.868E-06 0.0       1     
============================== ========= ========= ======