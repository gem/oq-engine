Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     2,852,175,627      
date           2019-10-01T06:32:38
engine_version 3.8.0-git66affb82eb
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
0      2.00000   444          444         
1      2.00000   208          208         
2      2.00000   149          149         
3      2.00000   534          534         
4      2.00000   298          298         
5      2.00000   239          239         
6      2.00000   474          474         
7      2.00000   238          238         
8      2.00000   179          179         
9      2.00000   409          409         
10     2.00000   173          173         
11     2.00000   114          114         
12     2.00000   465          465         
13     2.00000   229          229         
14     2.00000   170          170         
15     2.00000   411          411         
16     2.00000   175          175         
17     2.00000   116          116         
18     2.00000   483          483         
19     2.00000   247          247         
20     2.00000   188          188         
21     2.00000   582          582         
22     2.00000   346          346         
23     2.00000   287          287         
24     2.00000   516          516         
25     2.00000   280          280         
26     2.00000   221          221         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============ =======
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures speed  
========= ====== ==== ============ ========= ========= ============ =======
SFLT1     5      S    150          0.00587   1.00000   150          25,564 
SFLT2     3      S    384          0.00575   1.00000   384          66,783 
SFLT2     8      S    89           0.00534   1.00000   89           16,657 
SFLT1     0      S    60           0.00501   1.00000   60           11,978 
SFLT1     22     S    198          0.00491   1.00000   198          40,361 
SFLT1     24     S    132          0.00483   1.00000   132          27,318 
SFLT2     9      S    384          0.00463   1.00000   384          82,936 
SFLT2     12     S    384          0.00457   1.00000   384          83,991 
SFLT1     23     S    198          0.00445   1.00000   198          44,470 
SFLT2     10     S    148          0.00444   1.00000   148          33,315 
SFLT2     0      S    384          0.00441   1.00000   384          87,041 
SFLT1     1      S    60           0.00434   1.00000   60           13,809 
SFLT1     7      S    90           0.00420   1.00000   90           21,435 
SFLT2     18     S    384          0.00413   1.00000   384          93,029 
SFLT2     15     S    384          0.00404   1.00000   384          95,094 
SFLT2     6      S    384          0.00403   1.00000   384          95,314 
SFLT2     24     S    384          0.00377   1.00000   384          101,764
SFLT1     16     S    27           0.00376   1.00000   27           7,190  
SFLT2     20     S    89           0.00370   1.00000   89           24,055 
SFLT1     13     S    81           0.00367   1.00000   81           22,041 
========= ====== ==== ============ ========= ========= ============ =======

Computation times by source typology
------------------------------------
==== ========= ======
code calc_time counts
==== ========= ======
S    0.17138   54    
==== ========= ======

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.04660 0.00964 0.03374 0.07514 27     
preclassical       0.00683 0.00297 0.00299 0.01318 27     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ ========
task         sent                                             received
SourceReader apply_unc=52.47 KB ltmodel=5.62 KB fname=2.74 KB 97.19 KB
preclassical srcs=38.84 KB params=13.87 KB srcfilter=5.85 KB  10.25 KB
============ ================================================ ========

Slowest operations
------------------
====================== ======== ========= ======
calc_6476              time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     1.25811  0.44531   27    
composite source model 0.23186  0.0       1     
total preclassical     0.18441  0.0       27    
aggregate curves       0.00785  0.0       27    
store source_info      0.00298  0.0       1     
====================== ======== ========= ======