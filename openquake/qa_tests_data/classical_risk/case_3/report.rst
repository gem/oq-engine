Classical PSHA - Loss fractions QA test
=======================================

gem-tstation:/home/michele/ssd/calc_40515.hdf5 updated Mon Aug 22 12:15:00 2016

num_sites = 13, sitecol = 1.26 KB

Parameters
----------
============================ ================================
calculation_mode             'classical_risk'                
number_of_logic_tree_samples 1                               
maximum_distance             {u'Active Shallow Crust': 200.0}
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
sites_per_tile               10000                           
engine_version               '2.1.0-git8cbb23e'              
============================ ================================

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
====== ===================== =========== ======================= =================
grp_id gsims                 distances   siteparams              ruptparams       
====== ===================== =========== ======================= =================
0      ['ChiouYoungs2008()'] rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ===================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           1613         53    
================ ====== ==================== =========== ============ ======

Informational data
------------------
=============================== ============
classical_max_received_per_task 5,455       
classical_num_tasks             2           
classical_sent.monitor          1,896       
classical_sent.rlzs_by_gsim     1,044       
classical_sent.sitecol          1,346       
classical_sent.sources          3,894       
classical_tot_received          8,457       
hazard.input_weight             845         
hazard.n_imts                   1           
hazard.n_levels                 19          
hazard.n_realizations           1           
hazard.n_sites                  13          
hazard.n_sources                15          
hazard.output_weight            247         
hostname                        gem-tstation
require_epsilons                1           
=============================== ============

Exposure model
--------------
=============== ========
#assets         13      
#taxonomies     4       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 0.0    1   1   4         4         
DS       1.000 0.0    1   1   2         2         
UFB      1.000 0.0    1   1   2         2         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   13        13        
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            232       AreaSource   40     1         6.990E-04   0.0        1.975         1.975         1        
0            225       AreaSource   13     1         7.710E-04   0.0        0.313         0.313         1        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.001       0.0        2.287         2.287         2         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  1.147 1.174  0.317 1.977 2        
classical.memory_mb 2.309 0.354  2.059 2.559 2        
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                2.294     2.559     2     
making contexts                1.017     0.0       2,132 
reading composite source model 0.945     0.0       1     
get closest points             0.402     0.0       1,613 
computing poes                 0.302     0.0       1,613 
managing sources               0.033     0.0       1     
filtering sources              0.012     0.0       15    
store source_info              0.011     0.0       1     
reading exposure               0.006     0.0       1     
saving probability maps        0.002     0.0       1     
read poes                      0.002     0.0       1     
combine curves_by_rlz          0.002     0.0       1     
aggregate curves               7.098E-04 0.0       2     
building riskinputs            7.091E-04 0.0       1     
reading site collection        8.106E-06 0.0       1     
============================== ========= ========= ======