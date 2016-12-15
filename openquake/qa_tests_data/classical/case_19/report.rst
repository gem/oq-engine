SHARE OpenQuake Computational Settings
======================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_66995.hdf5 Wed Nov  9 08:15:53 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
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
============================ ====== ================= =========== ============ ============
source_model                 grp_id trt               num_sources eff_ruptures tot_ruptures
============================ ====== ================= =========== ============ ============
simple_area_source_model.xml 4      Subduction Inslab 1           7770         7,770       
============================ ====== ================= =========== ============ ============

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,156       
count_eff_ruptures_num_tasks             4           
count_eff_ruptures_sent.gsims            1,232       
count_eff_ruptures_sent.monitor          7,712       
count_eff_ruptures_sent.sitecol          2,308       
count_eff_ruptures_sent.sources          85,094      
count_eff_ruptures_tot_received          8,624       
hazard.input_weight                      777         
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
====== ========= ============ ============ ========= ========= =========
grp_id source_id source_class num_ruptures calc_time num_sites num_split
====== ========= ============ ============ ========= ========= =========
4      s46       AreaSource   7,770        0.0       1         0        
====== ========= ============ ============ ========= ========= =========

Computation times by source typology
------------------------------------
============ ========= ======
source_class calc_time counts
============ ========= ======
AreaSource   0.0       1     
============ ========= ======

Information about the tasks
---------------------------
================== ===== ========= ===== ===== =========
operation-duration mean  stddev    min   max   num_tasks
count_eff_ruptures 0.002 3.484E-04 0.001 0.002 4        
================== ===== ========= ===== ===== =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
reading composite source model   4.504     0.0       1     
managing sources                 0.255     0.0       1     
split/filter heavy sources       0.254     0.0       1     
filtering composite source model 0.016     0.0       1     
total count_eff_ruptures         0.007     0.0       4     
store source_info                4.950E-04 0.0       1     
aggregate curves                 5.531E-05 0.0       4     
reading site collection          3.791E-05 0.0       1     
saving probability maps          2.098E-05 0.0       1     
================================ ========= ========= ======