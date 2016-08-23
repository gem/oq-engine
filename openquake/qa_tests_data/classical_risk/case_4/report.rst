Classical Hazard-Risk QA test 4
===============================

gem-tstation:/home/michele/ssd/calc_41552.hdf5 updated Tue Aug 23 17:46:13 2016

num_sites = 6, sitecol = 969 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
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
sites_per_tile               10000                           
engine_version               '2.1.0-git5b04a6e'              
============================ ================================

Input files
-----------
======================== ============================================================
Name                     File                                                        
======================== ============================================================
exposure                 `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree          `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                  `job_haz.ini <job_haz.ini>`_                                
source                   `source_model.xml <source_model.xml>`_                      
source_model_logic_tree  `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_vulnerability `vulnerability_model.xml <vulnerability_model.xml>`_        
======================== ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ simple(2)       2/2             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== =================================== =========== ======================= =================
grp_id gsims                               distances   siteparams              ruptparams       
====== =================================== =========== ======================= =================
0      AkkarBommer2010() ChiouYoungs2008() rx rjb rrup vs30measured z1pt0 vs30 ztor mag rake dip
====== =================================== =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=2, rlzs=2)
  0,AkkarBommer2010(): ['<0,b1~b1,w=0.4>']
  0,ChiouYoungs2008(): ['<1,b1~b2,w=0.6>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 2           6405         160   
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,259       
count_eff_ruptures_num_tasks             2           
count_eff_ruptures_sent.monitor          1,876       
count_eff_ruptures_sent.rlzs_by_gsim     1,402       
count_eff_ruptures_sent.sitecol          1,066       
count_eff_ruptures_sent.sources          3,950       
count_eff_ruptures_tot_received          2,518       
hazard.input_weight                      2,276       
hazard.n_imts                            1           
hazard.n_levels                          19          
hazard.n_realizations                    2           
hazard.n_sites                           6           
hazard.n_sources                         39          
hazard.output_weight                     228         
hostname                                 gem-tstation
require_epsilons                         1           
======================================== ============

Exposure model
--------------
=============== ========
#assets         6       
#taxonomies     2       
deductibile     absolute
insurance_limit absolute
=============== ========

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
A        1.000 NaN    1   1   1         1         
W        1.000 0.0    1   1   5         5         
*ALL*    1.000 0.0    1   1   6         6         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            376       AreaSource   55     1         7.160E-04   0.0        0.0           0.0           0        
0            231       AreaSource   104    1         7.079E-04   0.0        0.0           0.0           0        
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.001       0.0        0.0           0.0           0         2     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 2.030     0.0       1     
managing sources               0.033     0.0       1     
filtering sources              0.029     0.0       39    
store source_info              0.009     0.0       1     
total count_eff_ruptures       0.003     0.0       2     
reading exposure               0.003     0.0       1     
aggregate curves               2.789E-05 0.0       2     
saving probability maps        2.193E-05 0.0       1     
reading site collection        5.960E-06 0.0       1     
============================== ========= ========= ======