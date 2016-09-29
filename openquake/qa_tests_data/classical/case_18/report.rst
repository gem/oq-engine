Demo Classical PSHA for Vancouver Schools
=========================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_54416.hdf5 Tue Sep 27 14:06:51 2016
engine_version                                 2.1.0-git1ca7123        
hazardlib_version                              0.21.0-git9261682       
============================================== ========================

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ================================
calculation_mode             'classical'                     
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 400.0}
investigation_time           1.0                             
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         5.0                             
complex_fault_mesh_spacing   5.0                             
width_of_mfd_bin             0.1                             
area_source_discretization   50.0                            
random_seed                  23                              
master_seed                  0                               
sites_per_tile               10000                           
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `nbc_asc_logic_tree.xml <nbc_asc_logic_tree.xml>`_          
job_ini                 `job.ini <job.ini>`_                                        
sites                   `vancouver_school_sites.csv <vancouver_school_sites.csv>`_  
source                  `vancouver_area_source.xml <vancouver_area_source.xml>`_    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================================== =============== ================
smlt_path weight source_model_file                                        gsim_logic_tree num_realizations
========= ====== ======================================================== =============== ================
b1        1.000  `vancouver_area_source.xml <vancouver_area_source.xml>`_ simple(3)       3/3             
========= ====== ======================================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================================================================================================================== ========= ========== ==========
grp_id gsims                                                                                                                                      distances siteparams ruptparams
====== ========================================================================================================================================== ========= ========== ==========
0      GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5') rhypo                mag       
====== ========================================================================================================================================== ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=3, rlzs=3)
  0,GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5'): ['<2,b1~b13,w=0.16>']
  0,GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5'): ['<0,b1~b11,w=0.16>']
  0,GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5'): ['<1,b1~b12,w=0.68>']>

Number of ruptures per tectonic region type
-------------------------------------------
========================= ====== ==================== =========== ============ ======
source_model              grp_id trt                  num_sources eff_ruptures weight
========================= ====== ==================== =========== ============ ======
vancouver_area_source.xml 0      Active Shallow Crust 1           2430         60    
========================= ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,643       
count_eff_ruptures_num_tasks             1           
count_eff_ruptures_sent.gsims            159,956     
count_eff_ruptures_sent.monitor          1,425       
count_eff_ruptures_sent.sitecol          473         
count_eff_ruptures_sent.sources          2,213       
count_eff_ruptures_tot_received          1,643       
hazard.input_weight                      60          
hazard.n_imts                            3           
hazard.n_levels                          36          
hazard.n_realizations                    3           
hazard.n_sites                           3           
hazard.n_sources                         1           
hazard.output_weight                     324         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ============ ====== ========= =========
grp_id source_id source_class weight calc_time num_sites
====== ========= ============ ====== ========= =========
0      VICM      AreaSource   60     0.0       0        
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
================== ===== ====== ===== ===== =========
operation-duration mean  stddev min   max   num_tasks
count_eff_ruptures 0.001 NaN    0.001 0.001 1        
================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
reading composite source model 0.024     0.0       1     
total count_eff_ruptures       0.001     0.0       1     
managing sources               0.001     0.0       1     
store source_info              4.549E-04 0.0       1     
reading site collection        8.798E-05 0.0       1     
saving probability maps        2.503E-05 0.0       1     
aggregate curves               1.788E-05 0.0       1     
============================== ========= ========= ======