Event-based PSHA with logic tree sampling
=========================================

Datastore /home/michele/ssd/calc_10569.hdf5 last updated Tue Apr 19 05:58:51 2016 on gem-tstation

num_sites = 3, sitecol = 831 B

Parameters
----------
============================ ===================
calculation_mode             'event_based'      
number_of_logic_tree_samples 10                 
maximum_distance             {'default': 200.0} 
investigation_time           50.0               
ses_per_logic_tree_path      10                 
truncation_level             3.0                
rupture_mesh_spacing         2.0                
complex_fault_mesh_spacing   2.0                
width_of_mfd_bin             0.2                
area_source_discretization   20.0               
random_seed                  23                 
master_seed                  0                  
oqlite_version               '0.13.0-git7c9cf8e'
============================ ===================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source                  `source_model1.xml <source_model1.xml>`_                    
source                  `source_model2.xml <source_model2.xml>`_                    
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
========= ====== ======================================== =============== ================
smlt_path weight source_model_file                        gsim_logic_tree num_realizations
========= ====== ======================================== =============== ================
b11       0.100  `source_model1.xml <source_model1.xml>`_ simple(3)       7/7             
b12       0.100  `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
========= ====== ======================================== =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ======================================================= =========== ============================= =================
trt_id gsims                                                   distances   siteparams                    ruptparams       
====== ======================================================= =========== ============================= =================
0      BooreAtkinson2008 CampbellBozorgnia2008 ChiouYoungs2008 rx rjb rrup z2pt5 vs30measured vs30 z1pt0 ztor mag rake dip
1      BooreAtkinson2008 CampbellBozorgnia2008                 rjb rrup    z2pt5 vs30                    ztor mag rake dip
====== ======================================================= =========== ============================= =================

Realizations per (TRT, GSIM)
----------------------------

::

  <RlzsAssoc(size=5, rlzs=10)
  0,BooreAtkinson2008: ['<3,b11,BA,w=0.1>', '<5,b11,BA,w=0.1>']
  0,CampbellBozorgnia2008: ['<4,b11,CB,w=0.1>', '<6,b11,CB,w=0.1>']
  0,ChiouYoungs2008: ['<0,b11,CY,w=0.1>', '<1,b11,CY,w=0.1>', '<2,b11,CY,w=0.1>']
  1,BooreAtkinson2008: ['<8,b12,BA,w=0.1>', '<9,b12,BA,w=0.1>']
  1,CampbellBozorgnia2008: ['<7,b12,CB,w=0.1>']>

Number of ruptures per tectonic region type
-------------------------------------------
================= ====== ==================== =========== ============ ======
source_model      trt_id trt                  num_sources eff_ruptures weight
================= ====== ==================== =========== ============ ======
source_model1.xml 0      Active Shallow Crust 1           1,405        61    
source_model2.xml 1      Active Shallow Crust 1           133          61    
================= ====== ==================== =========== ============ ======

=============== =====
#TRT models     2    
#sources        2    
#eff_ruptures   1,538
filtered_weight 122  
=============== =====

Informational data
------------------
======== ==============
hostname 'gem-tstation'
======== ==============

Slowest sources
---------------
============ ========= ============ ====== ========= =========== ========== =========
trt_model_id source_id source_class weight split_num filter_time split_time calc_time
============ ========= ============ ====== ========= =========== ========== =========
0            1         AreaSource   61     307       0.001       0.066      3.173    
1            1         AreaSource   61     307       0.001       0.067      1.686    
============ ========= ============ ====== ========= =========== ========== =========

Slowest operations
------------------
============================== ========= ========= ======
operation                      time_sec  memory_mb counts
============================== ========= ========= ======
total compute_gmfs_and_curves  7.766     0.0       41    
compute poes                   6.102     0.0       1,538 
total compute_ruptures         4.892     0.0       62    
make contexts                  1.484     0.0       1,538 
filtering ruptures             0.806     0.0       1,538 
saving ruptures                0.479     0.0       1     
managing sources               0.406     0.0       1     
bulding hazard curves          0.143     0.0       41    
reading composite source model 0.134     0.0       1     
splitting sources              0.133     0.0       2     
aggregating hcurves            0.091     0.0       121   
aggregate curves               0.024     0.0       183   
store source_info              0.010     0.0       1     
filtering sources              0.003     0.0       2     
reading site collection        4.411E-05 0.0       1     
============================== ========= ========= ======