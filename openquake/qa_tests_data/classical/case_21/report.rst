Classical Hazard QA Test, Case 21
=================================

============== ===================
checksum32     3,516,643,643      
date           2019-10-23T16:26:34
engine_version 3.8.0-git2e0d8e6795
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
0      0.00450   444          444         
1      0.00962   208          208         
2      0.01342   149          149         
3      0.00375   534          534         
4      0.00671   298          298         
5      0.00837   239          239         
6      0.00422   474          474         
7      0.00840   238          238         
8      0.01117   179          179         
9      0.00489   409          409         
10     0.01156   173          173         
11     0.01754   114          114         
12     0.00430   465          465         
13     0.00873   229          229         
14     0.01176   170          170         
15     0.00487   411          411         
16     0.01143   175          175         
17     0.01724   116          116         
18     0.00414   483          483         
19     0.00810   247          247         
20     0.01064   188          188         
21     0.00344   582          582         
22     0.00578   346          346         
23     0.00697   287          287         
24     0.00388   516          516         
25     0.00714   280          280         
26     0.00905   221          221         
====== ========= ============ ============

Slowest sources
---------------
========= ====== ==== ============ ========= ========= ============
source_id grp_id code num_ruptures calc_time num_sites eff_ruptures
========= ====== ==== ============ ========= ========= ============
SFLT2     0      S    384          0.00731   0.00260   384         
SFLT1     12     S    81           0.00575   0.01235   81          
SFLT2     15     S    384          0.00255   0.00260   384         
SFLT1     19     S    99           0.00254   0.01010   99          
SFLT2     18     S    384          0.00252   0.00260   384         
SFLT1     16     S    27           0.00251   0.03704   27          
SFLT2     20     S    89           0.00251   0.01124   89          
SFLT1     22     S    198          0.00251   0.00505   198         
SFLT2     21     S    384          0.00251   0.00260   384         
SFLT2     3      S    384          0.00245   0.00260   384         
SFLT1     1      S    60           0.00241   0.01667   60          
SFLT1     3      S    150          0.00241   0.00667   150         
SFLT2     24     S    384          0.00241   0.00260   384         
SFLT1     4      S    150          0.00240   0.00667   150         
SFLT2     8      S    89           0.00240   0.01124   89          
SFLT2     6      S    384          0.00240   0.00260   384         
SFLT1     0      S    60           0.00239   0.01667   60          
SFLT1     5      S    150          0.00238   0.00667   150         
SFLT1     10     S    25           0.00237   0.04000   25          
SFLT1     26     S    132          0.00234   0.00758   132         
========= ====== ==== ============ ========= ========= ============

Computation times by source typology
------------------------------------
==== =========
code calc_time
==== =========
S    0.10579  
==== =========

Duplicated sources
------------------
Found 0 unique sources and 12 duplicate sources with multiplicity 4.5: ['SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1' 'SFLT1'
 'SFLT2' 'SFLT2' 'SFLT2']

Information about the tasks
---------------------------
================== ======= ======= ======= ======= =======
operation-duration mean    stddev  min     max     outputs
SourceReader       0.08273 0.03051 0.03730 0.17775 27     
preclassical       0.00420 0.00221 0.00228 0.01199 27     
================== ======= ======= ======= ======= =======

Data transfer
-------------
============ ================================================ =========
task         sent                                             received 
SourceReader apply_unc=52.47 KB ltmodel=5.62 KB fname=2.74 KB 105.71 KB
preclassical srcs=38.83 KB params=14.95 KB srcfilter=5.88 KB  10.24 KB 
============ ================================================ =========

Slowest operations
------------------
====================== ======== ========= ======
calc_44531             time_sec memory_mb counts
====================== ======== ========= ======
total SourceReader     2.23374  0.50000   27    
composite source model 0.34275  0.0       1     
total preclassical     0.11333  0.0       27    
aggregate curves       0.01029  0.0       27    
store source_info      0.00246  0.0       1     
====================== ======== ========= ======