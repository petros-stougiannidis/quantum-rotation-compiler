import numpy as np
from itertools import combinations

from collections import OrderedDict


class RotationCircuit():
    
    def __init__(self, fractional_values, function):
        
        self.fractional_values = fractional_values.copy()
        self.register_size = len(self.fractional_values)
        self.function = function
        
        self.compile()

    def compile(self):

        # a list of dictionaries, where the k-th dictionary will store the k-fold controlled rotation gates
        circuit = [dict() for _ in range(self.register_size+1)]
        
        # compile a quantum lookup-table for the given function
        for input in self.possible_inputs(self.register_size):
            input_value = 0
            for bit in input:
                input_value += self.fractional_values[bit]
            circuit[len(input)][input] = self.function(input_value)
        
        # transform lookup-table
        for layer in range(len(circuit)-1):
            for control_qubits_in_lower_layer, rotation_value in circuit[layer].items():
                for layer_above in range(layer+1,len(circuit)):
                    for control_qubits_in_higher_layer in circuit[layer_above].keys():
                        if control_qubits_in_lower_layer.issubset(control_qubits_in_higher_layer):
                            circuit[layer_above][control_qubits_in_higher_layer] -= rotation_value
            
        self.circuit = circuit

        # update circuit size
        self.toffoli_count = 0
        self.ancilla_count = 0
        for layer, circuit in enumerate(self.circuit[2:]):
            self.toffoli_count += 2*(layer+1)*len(circuit)
            if len(circuit) > 0:
                self.ancilla_count = layer+1

    # generator for iterating over all possible inputs {}, {0}, ..., {0,1,...,n-1} for the quantum algorithm
    def possible_inputs(self,register_size):
        input_bits = set([index for index in range(0,register_size)])
        for hamming_weight in range(0,register_size+1):
            for input in combinations(input_bits, hamming_weight):
                yield frozenset(input)

    def approximate_up_to_an_error_of(self, error_upper_bound):
        
        # seperate the cheap from the expensive gates and sort the latter according to a contribution-to-cost ratio
        expensive_gates = dict()
        for layer in self.circuit[2:]:
            expensive_gates.update(layer)
        approximate_circuit = sorted(expensive_gates.items(), key = lambda gate: abs(gate[1]/(2*(len(gate[0])-1))))
        
        # Until the limit on the acceptable error is reached, omit the gate with the least impact
        current_error = 0
        while(len(approximate_circuit) > 0):
            error_contribution = abs(approximate_circuit[0][1])
            if error_contribution + current_error <= error_upper_bound:
                current_error += error_contribution
                approximate_circuit.pop(0)
            else:
                break

        # determine the toffoli count of the approximate circuit
        self.toffoli_count = np.sum([2*(len(control_qubits)-1) for control_qubits,_ in approximate_circuit])
        self.ancilla_count = np.max([len(control_qubits) for control_qubits,_ in approximate_circuit])-1

        # store the entire approximate circuit
        self.approximate_circuit = {**self.circuit[0],**self.circuit[1],**dict(approximate_circuit)}
        

c = RotationCircuit([2**(i) for i in range(3)],lambda x: x*x*x)
c.approximate_up_to_an_error_of(0)
print(c.approximate_circuit)