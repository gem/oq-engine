Event-based PSHA with logic tree sampling
=========================================

num_sites = 3, sitecol = 485 B

Parameters
----------
============================ ===========
calculation_mode             event_based
number_of_logic_tree_samples 10         
maximum_distance             200.0      
investigation_time           50.0       
ses_per_logic_tree_path      10         
truncation_level             3.0        
rupture_mesh_spacing         2.0        
complex_fault_mesh_spacing   2.0        
width_of_mfd_bin             0.2        
area_source_discretization   20.0       
random_seed                  23         
master_seed                  0          
concurrent_tasks             32         
============================ ===========

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
b11       0.1    `source_model1.xml <source_model1.xml>`_ simple(3)       7/3             
b12       0.1    `source_model2.xml <source_model2.xml>`_ simple(3)       3/3             
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

  <RlzsAssoc(5)
  0,BooreAtkinson2008: ['<3,b11,BA,w=0.1>', '<5,b11,BA,w=0.1>']
  0,CampbellBozorgnia2008: ['<4,b11,CB,w=0.1>', '<6,b11,CB,w=0.1>']
  0,ChiouYoungs2008: ['<0,b11,CY,w=0.1>', '<1,b11,CY,w=0.1>', '<2,b11,CY,w=0.1>']
  1,BooreAtkinson2008: ['<8,b12,BA,w=0.1>', '<9,b12,BA,w=0.1>']
  1,CampbellBozorgnia2008: ['<7,b12,CB,w=0.1>']>

Non-empty rupture collections
-----------------------------
=== ========= ==================== ============
col smlt_path TRT                  num_ruptures
=== ========= ==================== ============
0   b11       Active Shallow Crust 472         
1   b11       Active Shallow Crust 495         
2   b11       Active Shallow Crust 518         
3   b11       Active Shallow Crust 473         
4   b11       Active Shallow Crust 506         
5   b11       Active Shallow Crust 480         
6   b11       Active Shallow Crust 491         
7   b12       Active Shallow Crust 59          
8   b12       Active Shallow Crust 34          
9   b12       Active Shallow Crust 43          
=== ========= ==================== ============

Collections <-> realizations
----------------------------
=========== ============
Collections Realizations
0           0           
1           1           
2           2           
3           3           
4           4           
5           5           
6           6           
7           7           
8           8           
9           9           
=========== ============

Expected data transfer for the sources
--------------------------------------
=========================== =========
Number of tasks to generate 34       
Sent data                   500.37 KB
Total received data         1.42 MB  
Maximum received per task   86.07 KB 
=========================== =========