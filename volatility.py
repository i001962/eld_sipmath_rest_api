import logging
import time
from datetime import date

import numpy as np
import pandas as pd
import scipy
from metalog import metalog

from pricehistory import get_price_history

headers = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE"
}

"""
    Code borrowed from https://github.com/probability-management/PySIPmath/blob/main/PySIP/PySIP3library.py    
"""


def portfolio_shaper(sip_data, sip_metadata=[], dependence='independent', boundedness='u', bounds=[0, 1], term_saved=5,
                     seeds=[], setup_inputs=[]):
    if seeds != [] and len(seeds) < len(sip_data.columns):
        print("RNG list length must be equal to or greater than the number of SIPs.")
    elif setup_inputs != [] and len(setup_inputs["bounds"]) != len(sip_data.columns):
        print("List length of the input file must be equal to the number of SIPs.")
    else:
        slurp = sip_data  # Assigning some useful variables
        sip_count = len(slurp.columns)

        if not seeds:  # This section will create a random seed value for each SIP, or use an input 'rng' list
            rand = np.random.randint(1, 10000001)
            rnd_seeds = [1, rand, 0, 0]
            rngs = list()
            for i in range(sip_count):
                rngs.append({'name': 'hdr' + str(i + 1),
                             'function': 'HDR_2_0',
                             'arguments': {'counter': 'PM_Index',
                                           'entity': rnd_seeds[0],
                                           'varId': rnd_seeds[1] + i,
                                           'seed3': rnd_seeds[2],
                                           'seed4': rnd_seeds[3]}
                             })
        else:
            rngs = seeds

        # More set up to hold the copula information
        rng = list()
        for i in range(sip_count):
            rng.append('hdr' + str(i + 1))
        copula_layer = list()
        for i in range(sip_count):
            copula_layer.append('c' + str(i + 1))

        arguments = {'correlationMatrix': {'type': 'globalVariables',
                                           'value': 'correlationMatrix'},
                     'rng': rng}

        copdict = {'arguments': arguments,
                   'function': 'GaussianCopula',
                   'name': 'Gaussian',
                   'copulaLayer': copula_layer}

        copula = list()
        copula.append(copdict)
        rng = rngs

        if dependence == 'dependent':  # Holds the RNG and copula data if applicable
            oui = {'rng': rng,
                   'copula': copula}
        else:
            oui = {'rng': rng}
        # If the describe function is being used for default metadata,
        # then the names are being changed for the visual layer
        if not sip_metadata:
            slurp_meta = pd.DataFrame(slurp.describe())
            renames = slurp_meta.index.values
            renames[4] = 'P25'
            renames[5] = 'P50'
            renames[6] = 'P75'
        else:
            slurp_meta = sip_metadata

        if not setup_inputs:
            boundednessin = [boundedness] * sip_count
            if boundedness == 'u':
                boundsin = [[0, 1]] * sip_count
            else:
                boundsin = [bounds] * sip_count
            termsin = [term_saved] * sip_count
        else:
            boundednessin = setup_inputs['boundedness']
            boundsin = setup_inputs['bounds']
            for i in range(sip_count):
                if boundednessin[i] == 'u':
                    boundsin[i] = [0, 1]
            termsin = setup_inputs['term_saved']
        metadata = slurp_meta.to_dict()
        sips = list()  # Set up for the SIPs
        # This section creates the meta logs for each SIP,
        # and has a different version for the independent vs dependent case
        if dependence == 'dependent':
            for i in range(sip_count):
                mfitted = metalog.fit(np.array(slurp.iloc[:, i]).astype(float), bounds=boundsin[i],
                                      boundedness=boundednessin[i], term_limit=termsin[i], term_lower_bound=termsin[i])
                interp = scipy.interpolate.interp1d(mfitted['M'].iloc[:, 1], mfitted['M'].iloc[:, 0])
                interped = interp(np.linspace(min(mfitted['M'].iloc[:, 1]), max(mfitted['M'].iloc[:, 1]), 25)).tolist()
                a_coef = mfitted['A'].iloc[:, 1].to_list()
                metadata[slurp.columns[i]].update({'density': interped})
                if boundednessin[i] == 'u':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'copula',
                                       'name': 'Gaussian',
                                       'copulaLayer': 'c' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'sl':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'copula',
                                       'name': 'Gaussian',
                                       'copulaLayer': 'c' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'lowerBound': boundsin[i][0],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'su':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'copula',
                                       'name': 'Gaussian',
                                       'copulaLayer': 'c' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'upperBound': boundsin[i][0],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'b':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'copula',
                                       'name': 'Gaussian',
                                       'copulaLayer': 'c' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'lowerBound': boundsin[i][0],
                                             'upperBound': boundsin[i][1],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                sips.append(sipdict)
        else:
            for i in range(sip_count):
                mfitted = metalog.fit(np.array(slurp.iloc[:, i]).astype(float), bounds=boundsin[i],
                                      boundedness=boundednessin[i], term_limit=termsin[i], term_lower_bound=termsin[i])
                interp = scipy.interpolate.interp1d(mfitted['M'].iloc[:, 1], mfitted['M'].iloc[:, 0])
                interped = interp(np.linspace(min(mfitted['M'].iloc[:, 1]), max(mfitted['M'].iloc[:, 1]), 25)).tolist()
                a_coef = mfitted['A'].iloc[:, 1].to_list()
                metadata[slurp.columns[i]].update({'density': interped})
                if boundednessin[i] == 'u':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'rng',
                                       'name': 'hdr' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'sl':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'rng',
                                       'name': 'hdr' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'lowerBound': boundsin[i][0],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'su':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'rng',
                                       'name': 'hdr' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'upperBound': boundsin[i][0],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                if boundednessin[i] == 'b':
                    sipdict = {'name': slurp.columns[i],
                               'ref': {'source': 'rng',
                                       'name': 'hdr' + str(i + 1)},
                               'function': 'Metalog_1_0',
                               'arguments': {'lowerBound': boundsin[i][0],
                                             'upperBound': boundsin[i][1],
                                             'aCoefficients': a_coef},
                               'metadata': metadata[slurp.columns[i]]}
                sips.append(sipdict)
        # Creating the lower half of a correlation matrix for the copula section if applicable
        corrdata = pd.DataFrame(np.tril(slurp.corr()))
        corrdata.columns = slurp.columns
        corrdata.index = slurp.columns
        stackdf = corrdata.stack()
        truncstackdf = stackdf[stackdf.iloc[:] != 0]
        counter = truncstackdf.count()

        matrix = list()
        for i in range(counter):  # Gets our correlations in the correct format
            matrix.append({'row': truncstackdf.index.get_level_values(0)[i],
                           'col': truncstackdf.index.get_level_values(1)[i],
                           'value': truncstackdf[i]})

        value = {'columns': slurp.columns.to_list(),
                 'rows': slurp.columns.to_list(),
                 'matrix': matrix}

        if dependence == 'dependent':  # No global variables are added to the independent case
            global_variables = list()
            global_variables.append({'name': 'correlationMatrix', 'value': value})

            finaldict = {
                'name': 'Solace Native Library',
                'objectType': 'sipModel',
                'libraryType': 'SIPmath_3_0',
                'dateCreated': date.today().strftime("%m-%d-%Y"),
                'globalVariables': global_variables,
                'U01': oui,
                'sips': sips,
                'version': '1'}
        else:
            finaldict = {
                'name': 'Solace Native Library',
                'objectType': 'sipModel',
                'libraryType': 'SIPmath_3_0',
                'dateCreated': date.today().strftime("%m-%d-%Y"),
                'U01': oui,
                'sips': sips,
                'version': '1'}
        return finaldict


def get_price_change(price_history):
    price_change = {}
    for k, v in price_history.items():
        price_change[k] = list(map(lambda price_info: price_info['change'], v))
    return price_change


def compute_volatility(protocols, window=7, terms=3):
    logging.info("============================ <Volatility Starts> =====================================")
    if protocols is None:
        return {}
    if len(protocols) == 0:
        return {}

    start = time.time()
    price_history, token_map = get_price_history(protocols, window)
    if not price_history:
        return {}, []

    price_change_data = get_price_change(price_history)
    price_change = pd.DataFrame(price_change_data)
    terms = int(terms)
    logging.info("Calculating volatility..")
    volatility = portfolio_shaper(sip_data=price_change, sip_metadata=[], dependence='dependent', boundedness='u',
                                  bounds=[], term_saved=terms, seeds=[], setup_inputs=[])
    end = time.time()
    logging.info("Execution time(seconds): {}".format(end - start))
    logging.info("============================ <Volatility Ends> =====================================\n")
    return volatility, token_map
