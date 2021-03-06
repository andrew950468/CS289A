'''
Created on Apr 16, 2015

@author: antonio
'''
############# IMPORTS ############# 
from scipy import signal
import numpy as np
from scipy import io
import random
import cPickle as pickle
import os
import scipy.ndimage.filters as filters

def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size
    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w = arr.shape
    return (arr.reshape(h // nrows, nrows, -1, ncols)
               .swapaxes(1, 2)
               .reshape(-1, nrows, ncols))

def computeCV_Score(clf, data, labels, folds):
    """Compute cross validation on data over all folds, return accuracy"""
    i = 0
    j = 0
    accuracy = 0.0
    scores = []
    clf_local = clf
    # For each fold trained on...
    print np.shape(data), np.shape(labels)
    for i in range(folds):
        # Initialize variables
#         clf_local = clf
        j = 0
        accuracy = 0

        clf_local.fit(data[i], labels[i])
        # For each validation performed (k-1 total) on a fold
        for j in range(folds):
            if(j != i):
                predicted_Digits = clf_local.predict(data[j])
                for (elem1, elem2) in zip(predicted_Digits, labels[j]):
                    elem2 = elem2.tolist().index(1)
                    if elem1 == elem2:
                        accuracy += 1
                    else:
                        pass
            j += 1
        scores.append(100.0 * accuracy / ((folds - 1) * len(predicted_Digits)))
        print "Iteration(" + str(i) + ") Accuracy:", np.around(scores[-1], 1), "%"
        i += 1
    return np.array(scores), clf_local

def getDataNonMalik(imageComplete, data_type):
    """Return simple array of pixels (shuffled)"""
    if data_type == "train":
        # SHUFFLE
        random.shuffle(imageComplete)
    else:
        print "NOT SHUFFLING"
    # Arrays to hold the shuffled data and labels
    shuffledData = []
    shuffledLabels = []
    for elem in imageComplete:
        shuffledData.append((elem[0]).flatten())  # Use a simple array of pixels as the feature
        shuffledLabels.append((elem[1][0]))
    
    imageLabels_Vector = np.zeros((len(shuffledLabels), 10))
    ##### CONVERT LABELS to size(10) vectors ####
    for i in range(len(shuffledLabels)):
        imageLabels_Vector[i][shuffledLabels[i]] = 1
    shuffledLabels = imageLabels_Vector
    
    shuffledData = (shuffledData-np.mean(shuffledData))/np.std(shuffledData)
    
    print "Data Mean:", np.mean(shuffledData)
    print "Data Std:", np.std(shuffledData)

    return shuffledData, shuffledLabels, imageComplete

def getDataMalik(gauss_bool, imageData, imageLabels, data_type):
    """Take in image data, return histogram of oriented gradients"""
    imageComplete = zip(imageData, imageLabels)
    if data_type == "train":
        # SHUFFLE
        random.shuffle(imageComplete)
    else:
        print "NOT SHUFFLING"
    
    # shape of imageComplete is (60000,2) - transpose required
    imageData = np.array(imageComplete).T[0]
    imageLabels = np.array(imageComplete).T[1]

    imageLabels_Vector = np.zeros((len(imageLabels), 10))
    ##### CONVERT LABELS to size(10) vectors ####
    for i in range(len(imageLabels)):
        imageLabels_Vector[i][imageLabels[i]] = 1
    
    imageLabels = imageLabels_Vector
    ############# 
    # Ink Normalization
    ############# 
    for i in range(len(imageData)):
        imageData[i] -= np.mean(imageData[i])
        aux_norm = np.linalg.norm(imageData[i])
        if aux_norm != 0:
            imageData[i] /= aux_norm
        
    imageComplete = zip(imageData, imageLabels)
    # Arrays to hold the final shuffled data and labels
    shuffledData = []
    shuffledLabels = []

    n_bins = 9
    for ind in range(len(imageComplete)):
        if ind % 300 == 0:
            print 'feature extraction :' + str(np.around(ind * 100. / len(imageComplete), 1)) + ' % over'
        
        if gauss_bool:
            gaussFirst_x = filters.gaussian_filter1d(imageComplete[ind][0], 1, order=1, axis=0)
            gaussFirst_y = filters.gaussian_filter1d(imageComplete[ind][0], 1, order=1, axis=1)
            ori = np.array(np.arctan2(gaussFirst_y, gaussFirst_x))

        else:
            grad_filter = np.array([[-1, 0, 1]])
            gradx = signal.convolve2d(imageComplete[ind][0], grad_filter, 'same')
            grady = signal.convolve2d(imageComplete[ind][0], np.transpose(grad_filter), 'same')
            mag = np.sqrt(gradx ** 2 + grady ** 2)
            ori = np.array(np.arctan2(grady, gradx))
        
        ori_4_hist = list()
        ori_7_hist = list()
                     
        ori_4_1 = blockshaped(ori, 4, 4)
        ori_4_2 = blockshaped(ori[2:-2, 2:-2], 4, 4)
        for (elem1, elem2) in zip(ori_4_1, ori_4_2):
            ori_4_hist.append(np.histogram(elem1.flatten(), n_bins, (-np.pi, np.pi))[0])
            ori_4_hist.append(np.histogram(elem2.flatten(), n_bins, (-np.pi, np.pi))[0])
    
        ori_7_1 = (blockshaped(ori, 7, 7))
        ori_7_2 = (blockshaped(ori[3:-4, 3:-4], 7, 7))
        for elem1, elem2 in zip(ori_7_1, ori_7_2):
            ori_7_hist.append(np.histogram(elem1.flatten(), n_bins, (-np.pi, np.pi))[0])
            ori_7_hist.append(np.histogram(elem2.flatten(), n_bins, (-np.pi, np.pi))[0])
                
        features = np.append(ori_4_hist, ori_7_hist)
#         features = np.append(features, mag)
        features = (features - np.mean(features)) / np.linalg.norm(features)
        
        shuffledData.append(features)
        shuffledLabels.append((imageComplete[ind][1]))
        
    return shuffledData, shuffledLabels, imageComplete

def getDataPickle(imageData, imageLabels, data_type):
    """Loads image data stored as pickle object - if it doesnt exist, it creates it"""
    # Arrays to hold the shuffled data and labels
    shuffledData = list()
    shuffledLabels = list()

    if(os.path.isfile("./Results/" + data_type + "Data.p")):
        print('opening ' + data_type + ' data with pickle...')
        shuffledData = pickle.load(open("./Results/" + data_type + "Data.p", 'rb'))
        print('' + data_type + ' data successfully opened')
        print('opening ' + data_type + ' labels with pickle..')
        shuffledLabels = pickle.load(open("./Results/" + data_type + "Labels.p", 'rb'))
        print('' + data_type + ' labels successfully opened')
    else:
        print "Soft Error: PICKLE FILE NOT FOUND"
        shuffledData, shuffledLabels, _ = getDataMalik(False, imageData, imageLabels, data_type)
        print "Saving " + data_type + " Data as Pickle Object..."
        pickle.dump(shuffledData, open("./Results/" + data_type + "Data.p", 'wb'))
        pickle.dump(shuffledLabels, open("./Results/" + data_type + "Labels.p", 'wb'))
        print "Done Saving Data!"

        
    return shuffledData, shuffledLabels
