SHARE OpenQuake Computational Settings
======================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54422.hdf5 Tue Sep 27 14:07:21 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
============================================== ========================

num_sites = 1, sitecol = 739 B

Parameters
----------
============================ ==============================================================================================================================================================================================
calculation_mode             'classical'                                                                                                                                                                                   
number_of_logic_tree_samples 0                                                                                                                                                                                             
maximum_distance             {u'Volcanic': 200.0, u'Shield': 200.0, u'Active Shallow Crust': 200.0, u'Subduction Interface': 200.0, u'Stable Shallow Crust': 200.0, u'Subduction Deep': 200.0, u'Subduction Inslab': 200.0}
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
============================ ==============================================================================================================================================================================================

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
========= ====== ============================================================== ====================== ================
smlt_path weight source_model_file                                              gsim_logic_tree        num_realizations
========= ====== ============================================================== ====================== ================
b1        1.000  `simple_area_source_model.xml <simple_area_source_model.xml>`_ complex(4,4,1,0,0,5,2) 4/4             
========= ====== ============================================================== ====================== ================

Required parameters per tectonic region type
--------------------------------------------
====== ==================================================================================== ========== ========== ==============
grp_id gsims                                                                                distances  siteparams ruptparams    
====== ==================================================================================== ========== ========== ==============
4      AtkinsonBoore2003SSlab() LinLee2008SSlab() YoungsEtAl1997SSlab() ZhaoEtAl2006SSlab() rhypo rrup vs30       hypo_depth mag
====== ==================================================================================== ========== ========== ==============

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=4, rlzs=4)
  4,AtkinsonBoore2003SSlab(): ['<0,b1~@_@_@_@_b51_@_@,w=0.2>']
  4,LinLee2008SSlab(): ['<1,b1~@_@_@_@_b52_@_@,w=0.2>']
  4,YoungsEtAl1997SSlab(): ['<2,b1~@_@_@_@_b53_@_@,w=0.2>']
  4,ZhaoEtAl2006SSlab(): ['<3,b1~@_@_@_@_b54_@_@,w=0.4>']>

Number of ruptures per tectonic region type
-------------------------------------------
============================ ====== ================= =========== ============ ======
source_model                 grp_id trt               num_sources eff_ruptures weight
============================ ====== ================= =========== ============ ======
simple_area_source_model.xml 4      Subduction Inslab 1           7770         194   
============================ ====== ================= =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,137       
count_eff_ruptures_num_tasks             1           
count_eff_ruptures_sent.gsims            308         
count_eff_ruptures_sent.monitor          1,931       
count_eff_ruptures_sent.sitecol          433         
count_eff_ruptures_sent.sources          2,828       
count_eff_ruptures_tot_received          2,137       
hazard.input_weight                      194         
hazard.n_imts                            3           
hazard.n_levels                          78          
hazard.n_realizations                    1,280       
hazard.n_sites                           1           
hazard.n_sources                         1           
hazard.output_weight                     99,840      
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ============ ====== ========= =========
grp_id source_id source_class weight calc_time num_sites
====== ========= ============ ====== ========= =========
4      s46       AreaSource   194    0.0       0        
====== ========= ============ ====== ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ========= ====== ========= ========= =========
operation-duration mean      stddev min       max       num_tasks
count_eff_ruptures 9.210E-04 NaN    9.210E-04 9.210E-04 1        
================== ========= ====== ========= ========= =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 4.574     0.0       1     
total count_eff_ruptures       9.210E-04 0.0       1     
managing sources               6.931E-04 0.0       1     
store source_info              4.101E-04 0.0       1     
reading site collection        2.909E-05 0.0       1     
saving probability maps        2.313E-05 0.0       1     
aggregate curves               1.717E-05 0.0       1     
============================== ========= ========= ======