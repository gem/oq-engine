# Test 32 - Mutually exclusive sources within a Group

This test uses a logic tree with two branches each one with a group of sources: 

- The group in the first branch contains three mutually exclusive sources with a group probability of 0.01. We generate 500 realisations, hence we should expect 5 cases in which the source produces earthquakes. Five cases correspond to five ruptures since each source can generate at max one rupture. The weight for this branch is 0.2

- The group in the second contains 10 sources. In this case the group probability is not provided. By default this is taken equal to 1.0. Therefore, this group produces 500 ruptures. The weight for this branch is 0.8.

In terms of the components exercised this test is quite similar to what is in `src_mutex`.
