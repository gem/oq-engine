QA test for disaggregation case_1, taken from the disagg demo
=============================================================

============================================== ========================
gem-tstation:/home/michele/ssd/calc_67021.hdf5 Wed Nov  9 08:16:43 2016
engine_version                                 2.2.0-git54d01f4        
hazardlib_version                              0.22.0-git173c60c       
============================================== ========================

num_sites = 2, sitecol = 785 B

Parameters
----------
============================ ================================
calculation_mode             'disaggregation'                
number_of_logic_tree_samples 0                               
maximum_distance             {u'Active Shallow Crust': 200.0}
investigation_time           50.0                            
ses_per_logic_tree_path      1                               
truncation_level             3.0                             
rupture_mesh_spacing         5.0                             
complex_fault_mesh_spacing   5.0                             
width_of_mfd_bin             0.2                             
area_source_discretization   10.0                            
random_seed                  9000                            
master_seed                  0                               
============================ ================================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model.xml <source_model.xml>`_                      
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
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
====== ================= =========== ======================= =================
grp_id gsims             distances   siteparams              ruptparams       
====== ================= =========== ======================= =================
0      ChiouYoungs2008() rx rjb rrup vs30measured vs30 z1pt0 rake dip ztor mag
====== ================= =========== ======================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=1, rlzs=1)
  0,ChiouYoungs2008(): ['<0,b1~b1,w=1.0>']>

Number of ruptures per tectonic region type
-------------------------------------------
================ ====== ==================== =========== ============ ============
source_model     grp_id trt                  num_sources eff_ruptures tot_ruptures
================ ====== ==================== =========== ============ ============
source_model.xml 0      Active Shallow Crust 4           2236         2,236       
================ ====== ==================== =========== ============ ============

Informational data
------------------
======================================== ============
count_eff_ruptures_max_received_per_task 1,659       
count_eff_ruptures_num_tasks             6           
count_eff_ruptures_sent.gsims            534         
count_eff_ruptures_sent.monitor          8,502       
count_eff_ruptures_sent.sitecol          3,438       
count_eff_ruptures_sent.sources          10,121      
count_eff_ruptures_tot_received          9,950       
hazard.input_weight                      1,091       
hazard.n_imts                            2           
hazard.n_levels                          38          
hazard.n_realizations                    1           
hazard.n_sites                           2           
hazard.n_sources                         4           
hazard.output_weight                     76          
hostname                                 gem-tstation
======================================== ============

Slowest sources
---------------
====== ========= ================== ============ ========= ========= =========
grp_id source_id source_class       num_ruptures calc_time num_sites num_split
====== ========= ================== ============ ========= ========= =========
0      2         AreaSource         1,440        0.0       1         0        
0      1         PointSource        15           0.0       1         0        
0      4         ComplexFaultSource 164          0.0       1         0        
0      3         SimpleFaultSource  617          0.0       1         0        
====== ========= ================== ============ ========= ========= =========

Computation times by source typology
------------------------------------
================== ========= ======
source_class       calc_time counts
================== ========= ======
AreaSource         0.0       1     
ComplexFaultSource 0.0       1     
PointSource        0.0       1     
SimpleFaultSource  0.0       1     
================== ========= ======

Information about the tasks
---------------------------
================== ========= ========= ========= ========= =========
operation-duration mean      stddev    min       max       num_tasks
count_eff_ruptures 7.376E-04 1.011E-04 6.139E-04 8.850E-04 6        
================== ========= ========= ========= ========= =========

Slowest operations
------------------
================================ ========= ========= ======
operation                        time_sec  memory_mb counts
================================ ========= ========= ======
managing sources                 0.174     0.0       1     
split/filter heavy sources       0.171     0.0       1     
reading composite source model   0.059     0.0       1     
filtering composite source model 0.006     0.0       1     
total count_eff_ruptures         0.004     0.0       6     
store source_info                5.970E-04 0.0       1     
aggregate curves                 8.821E-05 0.0       6     
reading site collection          2.789E-05 0.0       1     
saving probability maps          2.718E-05 0.0       1     
================================ ========= ========= ======