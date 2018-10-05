Reduced Hazard Italy
====================

============== ===================
checksum32     3,187,729,294      
date           2018-10-05T03:04:48
engine_version 3.3.0-git48e9a474fd
============== ===================

num_sites = 90, num_levels = 30

Parameters
----------
=============================== ==================
calculation_mode                'event_based'     
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              200.0             
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            5.0               
complex_fault_mesh_spacing      10.0              
width_of_mfd_bin                0.2               
area_source_discretization      20.0              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     113               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
=============== ============================================
Name            File                                        
=============== ============================================
exposure        `exposure.xml <exposure.xml>`_              
gsim_logic_tree `gmpe_logic_tree.xml <gmpe_logic_tree.xml>`_
job_ini         `job.ini <job.ini>`_                        
site_model      `site_model.xml <site_model.xml>`_          
source          `as_model_full.xml <as_model_full.xml>`_    
source_model    `as_model_full.xml <as_model_full.xml>`_    
=============== ============================================

Exposure model
--------------
=============== ========
#assets         151     
#taxonomies     17      
deductibile     absolute
insurance_limit absolute
=============== ========

================= ======= ======= === === ========= ==========
taxonomy          mean    stddev  min max num_sites num_assets
CR/CDN/HBET:1-2   1.14286 0.37796 1   2   7         8         
CR/CDM/HBET:1-2   1.18182 0.60302 1   3   11        13        
CR/CDM/HBET:3-5   1.16667 0.57735 1   3   12        14        
CR/CDN/H:4        1.00000 0.0     1   1   2         2         
MUR/LWAL/HBET:5-8 1.20000 0.44721 1   2   5         6         
CR/CDM/HBET:6-8   1.50000 0.70711 1   2   2         3         
MUR/LWAL/H:3      1.20000 0.56061 1   3   15        18        
CR/CDM/SOS        1.42857 0.53452 1   2   7         10        
MUR/LWAL/HBET:1-2 1.30769 0.48038 1   2   13        17        
CR/CDN/SOS        1.42857 0.78680 1   3   7         10        
W/CDN/HBET:1-3    1.40000 0.69921 1   3   10        14        
CR/CDH/HBET:1-2   1.37500 1.06066 1   4   8         11        
CR/CDH/HBET:6-8   1.00000 0.0     1   1   3         3         
MUR/LWAL/H:4      1.60000 0.89443 1   3   5         8         
CR/CDH/HBET:3-5   1.28571 0.48795 1   2   7         9         
S/CDM/HBET:4-8    1.00000 0.0     1   1   2         2         
CR/CDN/H:3        1.00000 0.0     1   1   3         3         
*ALL*             1.67778 2.71421 0   15  90        151       
================= ======= ======= === === ========= ==========

Slowest sources
---------------
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
grp_id source_id  code gidx1 gidx2 num_ruptures calc_time split_time num_sites num_split weight
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======
0      AS_HRAS083 A    0     15    2,295        0.0       0.63394    0.0       25        0.0   
====== ========== ==== ===== ===== ============ ========= ========== ========= ========= ======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
A    0.0       1     
==== ========= ======

Duplicated sources
------------------
There are no duplicated sources

Information about the tasks
---------------------------
================== ======= ====== ======= ======= =======
operation-duration mean    stddev min     max     outputs
read_source_models 0.02540 NaN    0.02540 0.02540 1      
split_filter       0.02942 NaN    0.02942 0.02942 1      
================== ======= ====== ======= ======= =======

Data transfer
-------------
================== ======================================================================= ========
task               sent                                                                    received
read_source_models monitor=0 B fnames=0 B converter=0 B                                    2.84 KB 
split_filter       srcs=11.5 KB monitor=425 B srcfilter=220 B sample_factor=21 B seed=14 B 12.33 KB
================== ======================================================================= ========

Slowest operations
------------------
======================== ======== ========= ======
operation                time_sec memory_mb counts
======================== ======== ========= ======
reading exposure         0.05274  0.0       1     
updating source_info     0.03965  0.0       1     
total split_filter       0.02942  0.0       1     
total read_source_models 0.02540  0.0       1     
======================== ======== ========= ======