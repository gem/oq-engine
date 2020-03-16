Hazard South Africa
===================

============== ===================
checksum32     2_508_160_232      
date           2020-03-13T11:21:26
engine_version 3.9.0-gitfb3ef3a732
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

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.13115   36_461       488         
1      0.14789   19_539       426         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
18        0      A    480          0.00470   0.16667   282         
18        1      A    320          0.00464   0.25000   188         
21        0      A    84           0.00118   0.16667   66          
21        1      A    168          0.00118   0.08333   132         
20        0      A    23_199       4.611E-04 0.03030   132         
20        1      A    12_654       2.794E-04 0.05556   54          
22        1      A    52           2.387E-04 0.03846   52          
22        0      A    8            2.038E-04 0.25000   8.00000     
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.01289  
==== =========

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
preclassical       0.12492 0.08313 0.01453 0.22230 6      
read_source_model  0.04668 0.05624 0.00358 0.13294 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
================= ============================================ ========
task              sent                                         received
read_source_model converter=1.62 KB fname=495 B srcfilter=20 B 12.76 KB
preclassical      srcs=18.83 KB params=3.63 KB gsims=2.3 KB    2.27 KB 
================= ============================================ ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_66941                  time_sec memory_mb counts
=========================== ======== ========= ======
composite source model      1.01091  0.0       1     
total preclassical          0.74950  2.25781   6     
splitting/filtering sources 0.52598  0.75391   6     
total read_source_model     0.23339  0.46875   5     
store source_info           0.00219  0.0       1     
aggregate curves            0.00150  0.0       4     
=========================== ======== ========= ======