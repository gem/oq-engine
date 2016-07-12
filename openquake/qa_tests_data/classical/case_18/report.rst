Demo Classical PSHA for Vancouver Schools
=========================================

gem-tstation:/home/michele/ssd/calc_22599.hdf5 updated Tue May 31 15:37:55 2016

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===============================
calculation_mode             'classical'                    
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 400.0}
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
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

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
count_eff_ruptures_max_received_per_task 162,886     
count_eff_ruptures_num_tasks             30          
count_eff_ruptures_sent.monitor          4,878,840   
count_eff_ruptures_sent.rlzs_assoc       4,825,230   
count_eff_ruptures_sent.sitecol          14,190      
count_eff_ruptures_sent.siteidx          150         
count_eff_ruptures_sent.sources          40,960      
count_eff_ruptures_tot_received          4,886,580   
hazard.input_weight                      60          
hazard.n_imts                            3           
hazard.n_levels                          12          
hazard.n_realizations                    3           
hazard.n_sites                           3           
hazard.n_sources                         0           
hazard.output_weight                     324         
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
src_group_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            VICM      AreaSource   60     30        0.001       0.008      0.0      
============ ========= ============ ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
============ =========== ========== ========= ======
source_class filter_time split_time calc_time counts
============ =========== ========== ========= ======
AreaSource   0.001       0.008      0.0       1     
============ =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.096     0.0       1     
reading composite source model 0.024     0.0       1     
splitting sources              0.008     0.0       1     
total count_eff_ruptures       0.007     0.0       30    
store source_info              0.004     0.0       1     
filtering sources              0.001     0.0       1     
aggregate curves               3.502E-04 0.0       30    
reading site collection        8.392E-05 0.0       1     
============================== ========= ========= ======