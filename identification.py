# -*- coding: utf-8 -*-
"""
Created on Sat Feb 22 17:25:36 2014

@author: Lukasz Tracewski

Module for identification of kiwi calls
"""

import os
import pickle
import numpy as np
from collections import namedtuple
from utilities import contiguous_regions

Candidate = namedtuple('Candidate','start end density')


class KiwiFinder(object):
    """ Identification of kiwi calls """

    def __init__(self, app_config):
        """ Initialize Supervise Vector Machine with Gaussian kernel """
        model_path = os.path.join(app_config.program_directory, 'model.pkl')
        scaler_path = os.path.join(app_config.program_directory, 'scaler.pkl')
        with open(model_path, 'rb') as model_loader, open(scaler_path, 'rb') as scaler_loader:
            self._model = pickle.load(model_loader)
            self._scaler = pickle.load(scaler_loader)
        self.KiwiCounts = {'Male': 0, 'Female': 0, 'Male and Female': 0, 'None': 0}


    def _look_for_consecutive_calls(self, P, no_consecutive_calls=4):
        """ The most prominent feature of kiwi calls is their repetitive character - use it """
        kiwi = np.zeros(3, dtype='int')
        for i in np.arange(len(P)-no_consecutive_calls):
            # Following will be true if there are at least no_consecutive_calls next to each other
            if np.all(P[i:i + no_consecutive_calls] == P[i]):
                kiwi[P[i]] += 1

        # Check border conditions
        if np.all(P[:3] == P[0]):
            kiwi[P[0]] += 1
        if np.all(P[:3] == P[0]):
            kiwi[P[0]] += 1
        if np.all(P[-3:] == P[-1]):
            kiwi[P[-1]] += 1
        if np.all(P[-3:] == P[-1]):
            kiwi[P[-1]] += 1

        if kiwi[1] and kiwi[2] > 0:
            result = 'Male and Female'
        elif kiwi[1] > 0:
            result = 'Female'
        elif kiwi[2] > 0:
            result = 'Male'
        else:
            result = 'None'

        self.KiwiCounts[result] += 1

        return result

    def find_individual_calls(self, features):
        X = np.nan_to_num(features)
        X = self._scaler.transform(X)
        P = self._model.predict(X)
        return P

    def find_kiwi(self, individual_calls):
        result = self._look_for_consecutive_calls(individual_calls)
        if result == 'None':
            # if None were found relax the condition for number of consecutive calls
            result = self._look_for_consecutive_calls(individual_calls, 3)
        return result

    def find_candidates(self, condition, segments, rate, min_ind_call, min_calls_density):
        candidates = []
        result = contiguous_regions(condition)
        for start, end in result:
            length = end - start
            if length >= min_ind_call:
                region_start = segments[start][0]
                region_end = segments[start + length - 1][1]
                calls_density = (rate * length) / (region_end - region_start)
                if calls_density > min_calls_density:
                    candidates.append(Candidate(region_start, region_end, calls_density))
                else:
                    for i in np.arange(length - min_ind_call):
                        region_start = i
                        region_end = i + min_ind_call
                        calls_density = (rate * length) / (region_end - region_start)
                        if calls_density > min_calls_density:
                            candidates.append(Candidate(region_start, region_end, calls_density))
        return candidates

    def find_kiwi2(self, individual_calls, condition, segments, rate):
        min_calls_density = 0.5
        min_no_ind_calls = 4
        min_no_border_calls = 3
        females = []
        males = []
        females += self.find_candidates(individual_calls == 1, condition, segments, rate, min_no_ind_calls, min_calls_density)
        females += self.find_candidates(individual_calls[0:min_no_border_calls] == 1, condition, segments, rate, min_no_border_calls, min_calls_density)
        females += self.find_candidates(individual_calls[-min_no_border_calls:] == 1, condition, segments, rate, min_no_border_calls, min_calls_density)
        males += self.find_candidates(individual_calls == 2, condition, segments, rate, min_no_ind_calls, min_calls_density)
        males += self.find_candidates(individual_calls[0:min_no_border_calls] == 2, condition, segments, rate, min_no_border_calls, min_calls_density)
        males += self.find_candidates(individual_calls[-min_no_border_calls:] == 2, condition, segments, rate, min_no_border_calls, min_calls_density)

#    def find_kiwi_gender(self, gender, individual_calls, condition, segments, rate, )
#    def find_candidate(region_start, region_end, rate):
#        calls_density = (rate * length) / (region_end - region_start)
#        if calls_density > min_calls_density:
#            return Candidate(region_start, region_end, calls_density)
