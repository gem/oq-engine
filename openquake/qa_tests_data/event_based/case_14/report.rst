Hazard South Africa
===================

============== ===================
checksum32     2_508_160_232      
date           2020-03-31T07:29:22
engine_version 3.9.0-git805a678d6e
============== ===================

num_sites = 10, num_levels = 1, num_rlzs = 3

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    3                 
maximum_distance                {'default': 100.0}
investigation_time              100.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.1               
area_source_discretization      20.0              
pointsource_distance            {'default': {}}   
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        23                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gmmLT.xml <gmmLT.xml>`_                                    
job_ini                 `job.ini <job.ini>`_                                        
site_model              `Site_model_South_Africa.xml <Site_model_South_Africa.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                                    
======================= ============================================================

Composite source model
----------------------
=============================================================== ======= ================
smlt_path                                                       weight  num_realizations
=============================================================== ======= ================
b01_b1811_b1821_b1911_b1921_b2011_b2021_b2111_b2121_b2211_b2221 0.66667 2               
b01_b1812_b1822_b1913_b1923_b2012_b2022_b2112_b2123_b2214_b2223 0.33333 1               
=============================================================== ======= ================

Required parameters per tectonic region type
--------------------------------------------
====== ========================================== ========= ========== ==========
grp_id gsims                                      distances siteparams ruptparams
====== ========================================== ========= ========== ==========
0      '[AkkarEtAlRjb2014]' '[BooreAtkinson2008]' rjb       vs30       mag rake  
1      '[AkkarEtAlRjb2014]' '[BooreAtkinson2008]' rjb       vs30       mag rake  
====== ========================================== ========= ========== ==========

Slowest sources
---------------
========= ==== =========== ========= ========= ============
source_id code num_sources calc_time num_sites eff_ruptures
========= ==== =========== ========= ========= ============
18        A    2           0.00957   0.20000   470         
22        A    2           0.00365   0.06667   60          
21        A    2           0.00239   0.11111   198         
20        A    2           8.078E-04 0.03763   186         
========= ==== =========== ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01642  
==== =========

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
preclassical       0.07949 0.09271   0.00354 0.23176 10     
read_source_model  0.00247 1.507E-04 0.00230 0.00271 5      
================== ======= ========= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model converter=1.62 KB fname=495 B srcfilter=20 B 9.54 KB 
preclassical      srcs=23.56 KB params=6.22 KB gsims=3.84 KB   8.83 KB 
================= ============================================ ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_41331                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      0.82970  1.48438   1     
total preclassical          0.79490  2.12500   10    
splitting/filtering sources 0.54452  1.01172   10    
total read_source_model     0.01234  0.64844   5     
aggregate curves            0.00269  0.00781   8     
store source_info           0.00121  0.0       1     
=========================== ======== ========= ======