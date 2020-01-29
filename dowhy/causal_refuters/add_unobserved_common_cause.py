import copy
import logging
import numpy as np
import pandas as pd

import matplotlib
import matplotlib.pyplot as plt

from dowhy.causal_refuter import CausalRefutation
from dowhy.causal_refuter import CausalRefuter


class AddUnobservedCommonCause(CausalRefuter):

    """Add an unobserved confounder for refutation.

    Supports additional parameters that can be specified in the refute_estimate() method.

    - 'confounders_effect_on_treatment': how the simulated confounder affects the value of treatment. This can be linear (for continuous treatment) or binary_flip (for binary treatment)
    - 'confounders_effect_on_outcome': how the simulated confounder affects the value of outcome. This can be linear (for continuous outcome) or binary_flip (for binary outcome)
    - 'effect_strength_on_treatment': parameter for the strength of the effect of simulated confounder on treatment. For linear effect, it is the regression coeffient. For binary_flip, it is the probability that simulated confounder's effect flips the value of treatment from 0 to 1 (or vice-versa).
    - 'effect_strength_on_outcome': parameter for the strength of the effect of simulated confounder on outcome. For linear effect, it is the regression coeffient. For binary_flip, it is the probability that simulated confounder's effect flips the value of outcome from 0 to 1 (or vice-versa).

    TODO: Needs scaled version of the parameters and an interpretation module
    (e.g., in comparison to biggest effect of known confounder)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.effect_on_t = kwargs["confounders_effect_on_treatment"] if "confounders_effect_on_treatment" in kwargs else "binary_flip"
        self.effect_on_y = kwargs["confounders_effect_on_outcome"] if "confounders_effect_on_outcome" in kwargs else "linear"
        self.kappa_t = kwargs["effect_strength_on_treatment"]
        self.kappa_y = kwargs["effect_strength_on_outcome"]

    def refute_estimate(self):
        
        if not isinstance(self.kappa_t, np.ndarray) and not isinstance(self.kappa_y, np.ndarray): # Deal with single value inputs
            new_data = copy.deepcopy(self._data)
            new_data = self.include_confounders_effect(new_data, self.kappa_t, self.kappa_y)

            new_estimator = self.get_estimator_object(new_data, self._target_estimand, self._estimate)
            new_effect = new_estimator.estimate_effect()
            refute = CausalRefutation(self._estimate.value, new_effect.value,
                                    refutation_type="Refute: Add an Unobserved Common Cause")
            return refute

        else: # Deal with multiple value inputs
            
            if isinstance(self.kappa_t, np.ndarray) and isinstance(self.kappa_y, np.ndarray): # Deal with range inputs
                                
                # Get a 2D matrix of values
                x,y =  np.meshgrid(self.kappa_t, self.kappa_y) # x,y are both MxN
                
                results_matrix = np.random.rand(len(x),len(y)) # Matrix to hold all the results of NxM
                print(results_matrix.shape)
                orig_data = copy.deepcopy(self._data)
                
                for i in range(0,len(x[0])):
                    for j in range(0,len(y)):
                        new_data = self.include_confounders_effect(orig_data, x[0][i], y[j][0])
                        new_estimator = self.get_estimator_object(new_data, self._target_estimand, self._estimate)
                        new_effect = new_estimator.estimate_effect()
                        refute = CausalRefutation(self._estimate.value, new_effect.value,
                                                refutation_type="Refute: Add an Unobserved Common Cause")
                        logging.debug(refute)
                        results_matrix[i][j] = refute.estimated_effect[0] # Populate the results
                
                fig = plt.figure(figsize=(6,5))
                left, bottom, width, height = 0.1, 0.1, 0.8, 0.8
                ax = fig.add_axes([left, bottom, width, height]) 

                cp = plt.contourf(x, y, results_matrix)
                plt.colorbar(cp)
                ax.set_title('Effect of Unobserved Common Cause')
                ax.set_xlabel('Value of Linear Constant on Treatment')
                ax.set_ylabel('Value of Linear Constant on Outcome')
                plt.show()
                return results_matrix

            elif isinstance(self.kappa_t, np.ndarray):
                outcomes = np.random.rand(len(self.kappa_t))
                orig_data = copy.deepcopy(self._data)

                for i in range(0,len(self.kappa_t)):
                    new_data = self.include_confounders_effect(orig_data, self.kappa_t[i], self.kappa_y)
                    new_estimator = self.get_estimator_object(new_data, self._target_estimand, self._estimate)
                    new_effect = new_estimator.estimate_effect()
                    refute = CausalRefutation(self._estimate.value, new_effect.value,
                                            refutation_type="Refute: Add an Unobserved Common Cause")
                    logging.debug(refute)
                    outcomes[i] = refute.estimated_effect[0] # Populate the results

                fig = plt.figure(figsize=(6,5))
                left, bottom, width, height = 0.1, 0.1, 0.8, 0.8
                ax = fig.add_axes([left, bottom, width, height]) 

                plt.plot(self.kappa_t, outcomes)
                ax.set_title('Effect of Unobserved Common Cause')
                ax.set_xlabel('Value of Linear Constant on Treatment')
                ax.set_ylabel('New Effect')
                plt.show()    
                return outcomes

            elif isinstance(self.kappa_y, np.ndarray):
                outcomes = np.random.rand(len(self.kappa_y))
                orig_data = copy.deepcopy(self._data)

                for i in range(0, len(self.kappa_y)):
                    new_data = self.include_confounders_effect(orig_data, self.kappa_t, self.kappa_y[i])
                    new_estimator = self.get_estimator_object(new_data, self._target_estimand, self._estimate)
                    new_effect = new_estimator.estimate_effect()
                    refute = CausalRefutation(self._estimate.value, new_effect.value,
                                            refutation_type="Refute: Add an Unobserved Common Cause")
                    logging.debug(refute)
                    outcomes[i] = refute.estimated_effect[0] # Populate the results
                
                fig = plt.figure(figsize=(6,5))
                left, bottom, width, height = 0.1, 0.1, 0.8, 0.8
                ax = fig.add_axes([left, bottom, width, height])

                plt.plot(self.kappa_y, outcomes)
                ax.set_title('Effect of Unobserved Common Cause')
                ax.set_xlabel('Value of Linear Constant on Outcome')
                ax.set_ylabel('New Effect')
                plt.show() 
                return outcomes

    def include_confounders_effect(self, new_data, kappa_t, kappa_y):
        num_rows = self._data.shape[0]
        w_random=np.random.randn(num_rows)

        if self.effect_on_t == "binary_flip":
            new_data['temp_rand_no'] = np.random.random(num_rows)
            new_data.loc[new_data['temp_rand_no'] <= kappa_t, self._treatment_name ]  = 1- new_data[self._treatment_name]
            for tname in self._treatment_name:
                if pd.api.types.is_bool_dtype(self._data[tname]):
                    new_data = new_data.astype({tname: 'bool'}, copy=False)
            new_data.pop('temp_rand_no')
        elif self.effect_on_t == "linear":
            confounder_t_effect = kappa_t * w_random
            new_data[self._treatment_name] = new_data[self._treatment_name].values - np.ndarray(shape=(num_rows,1), buffer=confounder_t_effect)
        else:
            raise NotImplementedError("'" + self.effect_on_t + "' method not supported for confounders' effect on treatment")

        if self.effect_on_y == "binary_flip":
            new_data['temp_rand_no'] = np.random.random(num_rows)
            new_data.loc[new_data['temp_rand_no'] <= kappa_y, self._outcome_name ]  = 1- new_data[self._outcome_name]
            new_data.pop('temp_rand_no')
        elif self.effect_on_y == "linear":
            confounder_y_effect = kappa_y * w_random
            new_data[self._outcome_name] = new_data[self._outcome_name].values - np.ndarray(shape=(num_rows,1), buffer=confounder_y_effect)
        else:
            raise NotImplementedError("'" + self.effect_on_y+ "' method not supported for confounders' effect on outcome")
        return new_data

