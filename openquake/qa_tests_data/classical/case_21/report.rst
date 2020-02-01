Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     3_516_643_643      
date           2020-01-16T05:31:15
engine_version 3.8.0-git83c45f7244
============== ===================

num_sites = 1, num_levels = 4, num_rlzs = 27

Parameters
----------
=============================== ==================
calculation_mode                'preclassical'    
number_of_logic_tree_samples    0                 
maximum_distance                {'default': 200.0}
investigation_time              1.0               
ses_per_logic_tree_path         1                 
truncation_level                3.0               
rupture_mesh_spacing            2.0               
complex_fault_mesh_spacing      2.0               
width_of_mfd_bin                1.0               
area_source_discretization      10.0              
pointsource_distance            None              
ground_motion_correlation_model None              
minimum_intensity               {}                
random_seed                     106               
master_seed                     0                 
ses_seed                        42                
=============================== ==================

Input files
-----------
======================= ============================================================
Name                    File                                                        
======================= ============================================================
gsim_logic_tree         `gsim_logic_tree.xml <gsim_logic_tree.xml>`_                
job_ini                 `job.ini <job.ini>`_                                        
source_model_logic_tree `source_model_logic_tree.xml <source_model_logic_tree.xml>`_
======================= ============================================================

Composite source model
----------------------
====================== ======= =============== ================
smlt_path              weight  gsim_logic_tree num_realizations
====================== ======= =============== ================
b1_mfd1_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd1_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd1_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd1_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd1_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd1_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd1_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd1_mid_dip_dip60  0.03960 trivial(1)      1               
b1_mfd2_high_dip_dip30 0.01360 trivial(1)      1               
b1_mfd2_high_dip_dip45 0.04080 trivial(1)      1               
b1_mfd2_high_dip_dip60 0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip30  0.01360 trivial(1)      1               
b1_mfd2_low_dip_dip45  0.04080 trivial(1)      1               
b1_mfd2_low_dip_dip60  0.01360 trivial(1)      1               
b1_mfd2_mid_dip_dip30  0.04080 trivial(1)      1               
b1_mfd2_mid_dip_dip45  0.12240 trivial(1)      1               
b1_mfd2_mid_dip_dip60  0.04080 trivial(1)      1               
b1_mfd3_high_dip_dip30 0.01320 trivial(1)      1               
b1_mfd3_high_dip_dip45 0.03960 trivial(1)      1               
b1_mfd3_high_dip_dip60 0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip30  0.01320 trivial(1)      1               
b1_mfd3_low_dip_dip45  0.03960 trivial(1)      1               
b1_mfd3_low_dip_dip60  0.01320 trivial(1)      1               
b1_mfd3_mid_dip_dip30  0.03960 trivial(1)      1               
b1_mfd3_mid_dip_dip45  0.11880 trivial(1)      1               
b1_mfd3_mid_dip_dip60  0.03960 trivial(1)      1               
====================== ======= =============== ================

Required parameters per tectonic region type
--------------------------------------------
====== ================== ========= ========== ==========
grp_id gsims              distances siteparams ruptparams
====== ================== ========= ========== ==========
0      '[SadighEtAl1997]' rrup      vs30       mag rake  
1      '[SadighEtAl1997]' rrup      vs30       mag rake  
2      '[SadighEtAl1997]' rrup      vs30       mag rake  
3      '[SadighEtAl1997]' rrup      vs30       mag rake  
4      '[SadighEtAl1997]' rrup      vs30       mag rake  
5      '[SadighEtAl1997]' rrup      vs30       mag rake  
6      '[SadighEtAl1997]' rrup      vs30       mag rake  
7      '[SadighEtAl1997]' rrup      vs30       mag rake  
8      '[SadighEtAl1997]' rrup      vs30       mag rake  
9      '[SadighEtAl1997]' rrup      vs30       mag rake  
10     '[SadighEtAl1997]' rrup      vs30       mag rake  
11     '[SadighEtAl1997]' rrup      vs30       mag rake  
12     '[SadighEtAl1997]' rrup      vs30       mag rake  
13     '[SadighEtAl1997]' rrup      vs30       mag rake  
14     '[SadighEtAl1997]' rrup      vs30       mag rake  
15     '[SadighEtAl1997]' rrup      vs30       mag rake  
16     '[SadighEtAl1997]' rrup      vs30       mag rake  
17     '[SadighEtAl1997]' rrup      vs30       mag rake  
18     '[SadighEtAl1997]' rrup      vs30       mag rake  
19     '[SadighEtAl1997]' rrup      vs30       mag rake  
20     '[SadighEtAl1997]' rrup      vs30       mag rake  
21     '[SadighEtAl1997]' rrup      vs30       mag rake  
22     '[SadighEtAl1997]' rrup      vs30       mag rake  
23     '[SadighEtAl1997]' rrup      vs30       mag rake  
24     '[SadighEtAl1997]' rrup      vs30       mag rake  
25     '[SadighEtAl1997]' rrup      vs30       mag rake  
26     '[SadighEtAl1997]' rrup      vs30       mag rake  
====== ================== ========= ========== ==========

Realizations per (GRP, GSIM)
----------------------------

::

  <RlzsAssoc(size=27, rlzs=27)>

Number of ruptures per source group
-----------------------------------
====== ========= ============ ============
grp_id num_sites num_ruptures eff_ruptures
====== ========= ============ ============
0      0.00676   444          444         
1      0.01351   208          148         
2      0.02247   149          89          
3      0.00667   534          150         
4      NaN       298          0.0         
5      NaN       239          0.0         
6      0.01111   474          90          
7      NaN       238          0.0         
8      NaN       179          0.0         
9      0.04000   409          25          
10     NaN       173          0.0         
11     NaN       114          0.0         
12     0.01235   465          81          
13     NaN       229          0.0         
14     NaN       170          0.0         
15     0.03704   411          27          
16     NaN       175          0.0         
17     NaN       116          0.0         
18     0.01010   483          99          
19     NaN       247          0.0         
20     NaN       188          0.0         
21     0.00505   582          198         
22     NaN       346          0.0         
23     NaN       287          0.0         
24     0.00758   516          132         
25     NaN       280          0.0         
26     NaN       221          0.0         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT1     21     S    198          0.00558   0.00505   198         
SFLT2     2      S    89           0.00543   0.02247   89          
SFLT2     1      S    148          0.00496   0.01351   148         
SFLT1     24     S    132          0.00474   0.00758   132         
SFLT1     0      S    60           0.00451   0.01667   60          
SFLT1     12     S    81           0.00447   0.01235   81          
SFLT1     18     S    99           0.00423   0.01010   99          
SFLT1     3      S    150          0.00416   0.00667   150         
SFLT2     0      S    384          0.00342   0.00521   384         
SFLT1     6      S    90           0.00332   0.01111   90          
SFLT1     9      S    25           0.00243   0.04000   25          
SFLT1     15     S    27           0.00116   0.03704   27          
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.04841  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ========= ======= ======= =======
operation-duration mean    stddev    min     max     outputs
SourceReader       0.04375 0.00452   0.03582 0.05478 27     
preclassical       0.00545 9.606E-04 0.00413 0.00684 11     
================== ======= ========= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=52.47 KB ltmodel=5.62 KB fname=2.74 KB 80.81 KB
preclassical srcs=12.57 KB params=7.21 KB srcfilter=2.4 KB    4.15 KB 
============ ================================================ ========

Slowest operations
------------------
=========================== ======== ========= ======
calc_43315                  time_sec memory_mb counts
=========================== ======== ========= ======
total SourceReader          1.18137  0.0       27    
composite source model      0.19664  0.0       1     
total preclassical          0.05992  0.25391   11    
splitting/filtering sources 0.00389  0.0       11    
store source_info           0.00277  0.0       1     
aggregate curves            0.00264  0.0       11    
=========================== ======== ========= ======