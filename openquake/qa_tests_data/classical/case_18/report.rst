Demo Classical PSHA for Vancouver Schools
=========================================

gem-tstation:/home/michele/ssd/calc_40720.hdf5 updated Mon Aug 22 12:53:35 2016

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
engine_version               '2.1.0-git8cbb23e'              
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
====== ========================================================================================================================================== =============== ========== ============
grp_id gsims                                                                                                                                      distances       siteparams ruptparams  
====== ========================================================================================================================================== =============== ========== ============
0      GMPETable(gmpe_table='Wcrust_high_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_low_rhypo.hdf5') GMPETable(gmpe_table='Wcrust_med_rhypo.hdf5') set([u'rhypo']) set([])    set(['mag'])
====== ========================================================================================================================================== =============== ========== ============

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
=============================== ============
classical_max_received_per_task 4,895       
classical_num_tasks             30          
classical_sent.monitor          36,450      
classical_sent.rlzs_by_gsim     4,817,850   
classical_sent.sitecol          14,190      
classical_sent.sources          41,140      
classical_tot_received          146,763     
hazard.input_weight             60          
hazard.n_imts                   3           
hazard.n_levels                 12          
hazard.n_realizations           3           
hazard.n_sites                  3           
hazard.n_sources                1           
hazard.output_weight            324         
hostname                        gem-tstation
=============================== ============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
src_group_id source_id source_class weight split_num filter_time split_time cum_calc_time max_calc_time num_tasks
============ ========= ============ ====== ========= =========== ========== ============= ============= =========
0            VICM      AreaSource   60     30        0.001       0.008      25            1.271         30       
============ ========= ============ ====== ========= =========== ========== ============= ============= =========

Computation times by source typology
------------------------------------
============ =========== ========== ============= ============= ========= ======
source_class filter_time split_time cum_calc_time max_calc_time num_tasks counts
============ =========== ========== ============= ============= ========= ======
AreaSource   0.001       0.008      25            1.271         30        1     
============ =========== ========== ============= ============= ========= ======

Information about the tasks
---------------------------
=================== ===== ====== ===== ===== =========
measurement         mean  stddev min   max   num_tasks
classical.time_sec  0.844 0.181  0.624 1.272 30       
classical.memory_mb 0.010 0.056  0.0   0.305 30       
=================== ===== ====== ===== ===== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total classical                25        0.305     30    
computing poes                 23        0.0       2,430 
making contexts                0.939     0.0       2,430 
managing sources               0.054     0.0       1     
reading composite source model 0.023     0.0       1     
splitting sources              0.008     0.0       1     
store source_info              0.005     0.0       1     
saving probability maps        0.001     0.0       1     
aggregate curves               0.001     0.0       30    
filtering sources              0.001     0.0       1     
read poes                      7.241E-04 0.0       1     
reading site collection        8.917E-05 0.0       1     
============================== ========= ========= ======