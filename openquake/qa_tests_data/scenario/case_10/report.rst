Hazard France Reduced
=====================

============== ====================
checksum32     4_053_279_609       
date           2020-11-02T09:35:30 
engine_version 3.11.0-git82b78631ac
============== ====================

num_sites = 66, num_levels = 0, num_rlzs = ?

Parameters
----------
=============================== ==========
calculation_mode                'scenario'
number_of_logic_tree_samples    0         
maximum_distance                None      
investigation_time              None      
ses_per_logic_tree_path         1         
truncation_level                None      
rupture_mesh_spacing            5.0       
complex_fault_mesh_spacing      5.0       
width_of_mfd_bin                None      
area_source_discretization      None      
pointsource_distance            None      
ground_motion_correlation_model None      
minimum_intensity               {}        
random_seed                     42        
master_seed                     0         
ses_seed                        42        
=============================== ==========

Input files
-----------
======== ============================================
Name     File                                        
======== ============================================
exposure `Exposure_France.xml <Exposure_France.xml>`_
job_ini  `job.ini <job.ini>`_                        
======== ============================================

Exposure model
--------------
=========== ==
#assets     66
#taxonomies 22
=========== ==

======================= ========== ======= ====== === === =========
taxonomy                num_assets mean    stddev min max num_sites
CR/LWAL+CDN/H:2         1          1.00000 nan    1   1   1        
W/LWAL+CDN/H:2          5          1.00000 0%     1   1   5        
MUR+CL/LWAL+CDN/H:2     7          1.00000 0%     1   1   7        
CR/LFINF+CDM/HBET:3-5   2          1.00000 0%     1   1   2        
CR/LFINF+CDM/H:2        8          1.00000 0%     1   1   8        
CR/LWAL+CDM/H:2         7          1.00000 0%     1   1   7        
MUR+CL/LWAL+CDN/H:1     2          1.00000 0%     1   1   2        
CR/LFINF+CDM/H:1        6          1.00000 0%     1   1   6        
MUR+ST/LWAL+CDN/H:1     7          1.00000 0%     1   1   7        
W/LWAL+CDN/H:1          2          1.00000 0%     1   1   2        
W/LWAL+CDM/H:1          3          1.00000 0%     1   1   3        
CR/LWAL+CDN/HBET:3-5    1          1.00000 nan    1   1   1        
W/LWAL+CDM/H:2          1          1.00000 nan    1   1   1        
CR/LWAL+CDM/H:1         2          1.00000 0%     1   1   2        
CR/LWAL+CDM/HBET:3-5    3          1.00000 0%     1   1   3        
MUR+CL/LWAL+CDM/H:2     1          1.00000 nan    1   1   1        
CR+PC/LWAL+CDM/HBET:3-5 2          1.00000 0%     1   1   2        
CR/LWAL+CDH/H:2         1          1.00000 nan    1   1   1        
CR/LWAL+CDH/HBET:3-5    2          1.00000 0%     1   1   2        
MUR+ST/LWAL+CDN/H:2     1          1.00000 nan    1   1   1        
CR/LFINF+CDH/H:1        1          1.00000 nan    1   1   1        
CR/LFINF+CDH/H:2        1          1.00000 nan    1   1   1        
*ALL*                   6_843      0.00964 1013%  0   1   66       
======================= ========== ======= ====== === === =========

Information about the tasks
---------------------------
Not available

Data transfer
-------------
==== ==== ========
task sent received
==== ==== ========

Slowest operations
------------------
================ ======== ========= ======
calc_47213       time_sec memory_mb counts
================ ======== ========= ======
importing inputs 2.20920  1.26172   1     
reading exposure 0.01463  0.0       1     
================ ======== ========= ======