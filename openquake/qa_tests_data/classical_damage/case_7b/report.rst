Classical PSHA-Based Hazard
===========================

gem-tstation:/home/michele/ssd/calc_22572.hdf5 updated Tue May 31 15:37:02 2016

num_sites = 7, sitecol = 1015 B

Parameters
----------
============================ ===============================
calculation_mode             'classical_damage'             
number_of_logic_tree_samples 0                              
maximum_distance             {'Active Shallow Crust': 200.0}
investigation_time           50.0                           
ses_per_logic_tree_path      1                              
truncation_level             3.0                            
rupture_mesh_spacing         1.0                            
complex_fault_mesh_spacing   1.0                            
width_of_mfd_bin             0.1                            
area_source_discretization   20.0                           
random_seed                  42                             
master_seed                  0                              
sites_per_tile               10000                          
engine_version               '2.0.0-git4fb4450'             
============================ ===============================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
exposure                `exposure_model.xml <exposure_model.xml>`_                  
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job_haz.ini <job_haz.ini>`_                                
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
structural_fragility    `fragility_model.xml <fragility_model.xml>`_                
======================= ============================================================

Composite source model
----------------------
========= ====== ====================================== =============== ================
smlt_path weight source_model_file                      gsim_logic_tree num_realizations
========= ====== ====================================== =============== ================
b1        1.000  `source_model.xml <source_model.xml>`_ trivial(1)      1/1             
========= ====== ====================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================ ========= ========== ==========
grp_id gsims            distances siteparams ruptparams
====== ================ ========= ========== ==========
0      SadighEtAl1997() rrup      vs30       rake mag  
====== ================ ========= ========== ==========

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,SadighEtAl1997(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ======
source_model     grp_id trt                  num_sources eff_ruptures weight
================ ====== ==================== =========== ============ ======
source_model.xml 0      Active Shallow Crust 1           1694         1,694 
================ ====== ==================== =========== ============ ======

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 2,673       
count_eff_ruptures_num_tasks             14          
count_eff_ruptures_sent.monitor          34,426      
count_eff_ruptures_sent.rlzs_assoc       10,346      
count_eff_ruptures_sent.sitecol          7,742       
count_eff_ruptures_sent.siteidx          70          
count_eff_ruptures_sent.sources          15,499      
count_eff_ruptures_tot_received          37,422      
hazard.input_weight                      1,694       
hazard.n_imts                            3           
hazard.n_levels                          8.000       
hazard.n_realizations                    1           
hazard.n_sites                           7           
hazard.n_sources                         0           
hazard.output_weight                     168         
hostname                                 gem-tstation
require_epsilons                         False       
======================================== ============

Exposure model
--------------
=========== =
#assets     7
#taxonomies 3
=========== =

======== ===== ====== === === ========= ==========
taxonomy mean  stddev min max num_sites num_assets
Concrete 1.000 0.0    1   1   2         2         
Steel    1.000 0.0    1   1   2         2         
Wood     1.000 0.0    1   1   3         3         
*ALL*    1.000 0.0    1   1   7         7         
======== ===== ====== === === ========= ==========

Slowest sources
---------------
============ ========= ================= ====== ========= =========== ========== =========
src_group_id source_id source_class      weight split_num filter_time split_time calc_time
============ ========= ================= ====== ========= =========== ========== =========
0            1         SimpleFaultSource 1,694  15        0.002       0.070      0.0      
============ ========= ================= ====== ========= =========== ========== =========

Computation times by source typology
------------------------------------
================= =========== ========== ========= ======
source_class      filter_time split_time calc_time counts
================= =========== ========== ========= ======
SimpleFaultSource 0.002       0.070      0.0       1     
================= =========== ========== ========= ======

Information about the tasks
---------------------------
Not available

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
managing sources               0.085     0.0       1     
splitting sources              0.070     0.0       1     
reading composite source model 0.010     0.0       1     
store source_info              0.008     0.0       1     
reading exposure               0.006     0.0       1     
total count_eff_ruptures       0.003     0.0       14    
filtering sources              0.002     0.0       1     
aggregate curves               3.014E-04 0.0       14    
reading site collection        7.153E-06 0.0       1     
============================== ========= ========= ======