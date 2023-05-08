# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Module :mod:`openquake.hmtk.seismicity.declusterer.dec_zaliapin`
defines the Zaliapin declustering algorithm


"""
import numpy as np
import datetime
import matplotlib.dates as mdates

from openquake.hmtk.seismicity.declusterer.base import (
    BaseCatalogueDecluster, DECLUSTERER_METHODS)

from openquake.hazardlib.geo.geodetic import geodetic_distance, distance, _prepare_coords 

#from openquake.hmtk.seismicity.utils import relative_time

from sklearn import mixture
#from pymap3d import geodetic2ned


@DECLUSTERER_METHODS.add(
    "decluster",
    fractal_dim=np.float,  # spatial weighting factor
    b_value=np.float,      # magnitude weighting factor
)
class Zaliapin(BaseCatalogueDecluster):
    """
    Implements the declustering method of Zaliapin and Ben-Zion (2013), based on a nearest-neighbour distance metric.
    
    Implemented in Python by CG Reyes.
    Modified to return mainshocks (largest event per cluster) and to give the option for
    stochastic declustering (defaults to this when no threshold is specified). 
     
    """

    def __init__(self):
        pass

    def decluster(self, catalogue, config):
        """Zaliapin's declustering code

        :param catalogue:
            Earthquake catalog to examine
        :param config:
            Dictionary containing 
            1. values for fractal dimension `frac_dim` and Gutenberg-Richter `b-value`
            2. Method used to choose which events to keep. Use `Threshold = ` to specify a float value for probability at which to keep an event.
               If `Stochastic = True` (or no threshold is provided) a stochastic declustering will be implemented.
               A seed for the stochastic method can be specified with the `stoch_seed` parameter (will default to 5 if not included)
            3. Optional flag to use depths when calculating event distances. Note that the fractal dimension should correspond to the number of dimensions in the model.
               (Zaliapin and Ben-Zion defaults are 1.6 for 2D and 2.4 for 3D distances and these values are generally used in the literature).
            
        :return:
            probability [0..1] that each event is a member of a cluster, and optionally (if
            config['nearest_neighbor_dist'] is true) return the nearest neighbor distances, mainshock flag, root (first) event in cluster and leaf depth of cluster.
        """

        if 'depth' in config and 'depth' == True:
            nnd, nni = self.getnnd(catalogue, config['fractal_dim'], config['b_value'], depth = True)
            
        else:
            nnd, nni = self.getnnd(catalogue, config['fractal_dim'], config['b_value'], depth = False)

        probability_of_independence = self.gaussianmixturefit(nnd)
        
        if 'threshold' in config and isinstance(s, (int,float)):
            threshold = config['threshold']
            root, ld, ms_flag = cluster_number(catalogue, nni, probability_of_independence, threshold = 0.5, stochastic = False)
           
        else:
            root, ld, ms_flag = cluster_number(catalogue, nni, probability_of_independence,  stochastic = True)
                 

        if 'output_nearest_neighbor_distances' in config and config['output_nearest_neighbor_distances']:
            return probability_of_independence, nnd, ms_flag, root, ld
        
        return root, ms_flag

   
    @staticmethod
    def getnnd(catalogue, d_f=1.6, b=1.0, depth = False):
        """
        Identifies nearest neighbour parent and distance for each event.
       
        :param catalogue:
            an earthquake catalogue
        :param d_f:
            fractal dimension (default 1.6 for 2D, recommend ~2.4 for 3D)
        :param b:
            b-value for the catalogue
        :param depth:
            flag to include depths 

        :return:
            nearest neighbor distances, index of nearest neighbour as numpy arrays
        """
            
        # set up variables for later            
        nearest_distance=[0]*len(catalogue.data['latitude'])
        nearest_index=[0]*len(catalogue.data['latitude'])
        
        if (depth == True):    
            depth = catalogue.data['depth']
            # Set nan depths to 0
            depth[np.isnan(depth)] = 0
        else: depth = np.zeros(len(catalogue))
        
        # Is there a faster/better way to do this? Probably yes
        # TODO: Figure it out!
        time=[0]*len(catalogue)        
        # Change date and time data into one list of datetimes in years (ie 1980.25)       
        for i in range(len(time)):
            time[i]=datetime.datetime(catalogue.data['year'][i], catalogue.data['month'][i], catalogue.data['day'][i],catalogue.data['hour'][i], catalogue.data['minute'][i],np.int(catalogue.data['second'][i]))
            time[i]=mdates.date2num(time[i])
            # date2num gives days, change to years
            time[i]= (time[i] -1)/365.25

            
        for j in range(1, len(catalogue)):
            # Calculate spatial distance between events
            dist = distance(catalogue.data['latitude'][j], catalogue.data['longitude'][j], depth[j], catalogue.data['latitude'][:j], catalogue.data['longitude'][:j], depth[:j])
                      
            time_diff= time[j]-time[:j]
            # If time difference is zero, set to very small value
            time_diff[time_diff == 0] = 0.0000001
            # Similarly with spatial distances = 0
            dist[dist < 0.1] = 0.1
            # ZBZ interevent distance is product of time_diff*(10^(b*Mi))*spat_dist^(d_f)
            interevent_distance = time_diff*(10**(-b*catalogue.data['magnitude'][:j]))*(dist**d_f)

            # Record index of nearest neighbour (needed to reconstruct the clusters) and the nnd (smallest nnd)
            nearest_index[j] = np.argmin(interevent_distance)
            nearest_distance[j] = np.min(interevent_distance)
            
            
        ## Set zeroth event to mean NND (doesn't really matter what we do with this)  
        nearest_distance[0]= np.mean(nearest_distance)
            
        return(nearest_distance, nearest_index)
        
    @staticmethod
    def gaussianmixturefit(nnd):
        """
        fit Gaussian mixture distribution to nearest neighbour distances (Zaliapin and Ben-Zion 2013) and calculate probability of independence from mixture fit.
        
        :param nnd:
            nearest neighbour distances for each event
        
        :return:
            probability of independence of event based on mixture fit
        """
        log_nearest_neighbor_dist = np.log10(nnd)
        samples = log_nearest_neighbor_dist[np.isfinite(log_nearest_neighbor_dist)]
        samples = samples.reshape(-1,1)
        
        # find two gaussians that fit the nearest-neighbor-distances
        clf = mixture.GaussianMixture(n_components=2, covariance_type='full')
        clf.fit(samples)
        

        probability_of_independence = np.zeros_like(log_nearest_neighbor_dist)

        # calculate the probabilities that it belongs to each of the gaussian curves (2 columns of probabilities)
        prediction = clf.predict_proba(samples)

        # keep only the chance that this is a background event (the column matching the gaussian model's largest mean)
        probability_of_independence[np.isfinite(log_nearest_neighbor_dist)] = prediction[:, np.argmax(clf.means_)]

        probability_of_independence[0] = 1  # first event, by definition, cannot depend upon prior events
        probability_of_independence[np.isnan(probability_of_independence)] = 0
        
        return probability_of_independence


# TODO: Option to skip the reconstruction phase - then this should be directly comparable to the original version

## function to reconstruct clusters - need this to identify mainshocks rather than earliest events

def cluster_number(catalogue, nearest_index, prob_ind, threshold = 0.5, stochastic = True, stoch_seed = 5):
    """
    Identifies head node (first event in cluster) and number of iterations of while loop to get to it
    (ie how deep in cluster event is; 1st, 2nd, 3rd generation etc). 
    
    :param catalogue:
        an earthquake catalogue
    
    :param nearest_index:
        index of event's nearest neighbour (output of getnnd)
    
    :param prob_ind:
        Probability event is independent (output of gaussianmixturefit)
        
    :param threshold:
        Threshold of independence probability at which to consider an event independent. Specified in config file or default to 0.5.
    
    :param stochastic:
        Instead of using a fixed threshold, use a stochastic method to thin clustered events
        
    :param stoch_seed:
        Seed value for stochastic thinning to assure reproducibility. Set by default if not specified.
        
    :return:
        arrays of root, event depth, mainshock flag
        
    """
         
    n_id = range(len(catalogue)+1) 
    root = np.zeros(len(catalogue))
    ld = np.zeros(len(catalogue))
    indep_flag = np.zeros(len(catalogue))
     
     
    if stochastic == True:
        # set seed for reproducible results when using stochastic method
        np.random.seed(stoch_seed)
        indep_flag = 1*prob_ind > np.random.uniform(0,1)
     
    else:
        indep_flag = 1*(prob_ind > threshold)
     
    parent = nearest_index*(1-indep_flag)     

    for i in range(len(catalogue)):
        
        p = parent[i]
        if(p == 0):
            root[i] = i
            ld[i] = 0
        else:    
            while (p != 0):
                root[i] = p
                ld[i] = ld[i] +1
                p = parent[p]
    
    clust_heads = np.unique(root)
    MS = clust_heads.astype(int)
    
    for j in range(len(clust_heads)):
        # locate all events that are part of this cluster
        idx = np.argwhere(np.isin(root, clust_heads[j])).ravel()
        # collect all magnitudes
        mags = catalogue.data['magnitude'][idx]
        if len(mags) > 0:
            # find mainshock and add to MS 
            MS_rel = np.argmax(mags)
            MS[j] = idx[MS_rel]
    
    ms_flag = np.zeros(len(catalogue))
    ms_flag[MS] = 1
    
    return root, ld, ms_flag


#if __name__ == "__main__":

#    import os
#    import numpy as np

#    from openquake.hmtk.parsers.catalogue import CsvCatalogueParser
#    import pytest

#    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../tests/seismicity/declusterer/data')
#    BASE_TEST_PATH = os.path.join(os.path.dirname(__file__), '../../tests/seismicity/declusterer/dec_zaliapin_test.py')

#    flnme = 'zaliapin_test_catalogue.csv'
#    filename = os.path.join(BASE_DATA_PATH, flnme)
#    print('Testing with:', filename)
#    parser = CsvCatalogueParser(filename)
#    cat = parser.read_file()
#    comment = cat['comment']  # comment is: IndependentProbability,log10nearestDistances

#    indep_prob, log10_nearestdists = np.array([s.split(',') for s in comment], dtype=float).T
    # nearest_dists = [10. ** np.float(s.split(',')[1]) for s in comment]
#    nearest_dists = 10 ** log10_nearestdists

 #   config = {'fractal_dim': 2., 'b_value': 1.0, 'output_nearest_neighbor_distances': True}

 #   dec = Zaliapin()
 #   _, nearest_neighbor_dists = dec.decluster(cat, config)
 #   for n1, n2 in zip(np.round(nearest_neighbor_dists), np.round(nearest_dists)):
 #       if np.isnan(n1):
 #           assert np.isnan(n2)
 #       else:
 #           assert n1 == n2, f"{n1:.4f} vs {n2:.4f}"

#    pytest.main(['-v', BASE_TEST_PATH])
    

