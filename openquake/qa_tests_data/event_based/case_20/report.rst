British Columbia With Vs30
==========================

============== ===================
checksum32     226_163_923        
date           2020-01-16T05:31:00
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 2, num_levels = 3, num_rlzs = ?

Parameters
----------
=============================== ========================================================================
calculation_mode                'event_based'                                                           
number_of_logic_tree_samples    0                                                                       
maximum_distance                {'default': 800.0, 'Active Shallow Offshore': 800.0}                    
investigation_time              20.0                                                                    
ses_per_logic_tree_path         1                                                                       
truncation_level                3.0                                                                     
rupture_mesh_spacing            5.0                                                                     
complex_fault_mesh_spacing      10.0                                                                    
width_of_mfd_bin                0.1                                                                     
area_source_discretization      15.0                                                                    
pointsource_distance            None                                                                    
ground_motion_correlation_model None                                                                    
minimum_intensity               {'SA(0.3)': 0.001, 'SA(0.6)': 0.001, 'SA(1.0)': 0.001, 'default': 0.001}
random_seed                     24                                                                      
master_seed                     0                                                                       
ses_seed                        23                                                                      
=============================== ========================================================================

Input files
-----------
======================= =====================================================
Name                    File                                                 
======================= =====================================================
exposure                `BC_Exposure.xml <BC_Exposure.xml>`_                 
gsim_logic_tree         `gmmLT_analytical.xml <gmmLT_analytical.xml>`_       
job_ini                 `job.ini <job.ini>`_                                 
site_model              `vs30_a.xml <vs30_a.xml>`_ `vs30_b.xml <vs30_b.xml>`_
source_model_logic_tree `ssmLT.xml <ssmLT.xml>`_                             
======================= =====================================================

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      NaN       8_778        0.0         
1      NaN       15_618       0.0         
2      NaN       8_778        0.0         
3      NaN       8_778        0.0         
4      NaN       15_618       0.0         
====== ========= ============ ============

Exposure model
--------------
=========== =
#assets     2
#taxonomies 2
=========== =

========== ======= ======= === === ========= ==========
taxonomy   mean    stddev  min max num_sites num_assets
RES1-W1-HC 1.00000 NaN     1   1   1         1         
RES1-W1-LC 1.00000 NaN     1   1   1         1         
*ALL*      0.22222 0.44096 0   1   9         2         
========== ======= ======= === === ========= ==========

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
A    0.0      
==== =========

Duplicated sources
------------------
Found 0 unique sources and 2 duplicate sources with multiplicity 2.5: ['OFS' 'OFS']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.05873 0.01272 0.04735 0.07553 5      
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ =========================================== ========
task         sent                                        received
SourceReader apply_unc=8.64 KB ltmodel=985 B fname=570 B 17.68 KB
============ =========================================== ========

Slowest operations
------------------
====================== ======== ========= ======
calc_43273             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     0.29364  0.28125   5     
composite source model 0.10041  0.95312   1     
reading exposure       0.00183  0.0       1     
====================== ======== ========= ======