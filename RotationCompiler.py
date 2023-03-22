import numpy as np
from itertools import combinations
import time

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
        for input in self.possible_inputs():
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

        # reassemble and store the circuit
        self.circuit = dict()
        for layer in circuit:
            self.circuit.update(layer)
        
        self.update_circuit_size()

    # generator for iterating over all possible inputs {}, {0}, ..., {0,1,...,n-1} for the quantum algorithm
    def possible_inputs(self):
        input_bits = set([index for index in range(0,self.register_size)])
        for hamming_weight in range(0,self.register_size+1):
            for input in combinations(input_bits, hamming_weight):
                yield frozenset(input)
    
    def update_circuit_size(self):
        self.toffoli_count = np.sum([2*(len(control_qubits)-1) for control_qubits in self.circuit.keys()])
        self.ancilla_count = np.max([len(control_qubits) for control_qubits in self.circuit.keys()])-1

    def approximate_up_to_an_error_of(self, error_upper_bound):
        
        # seperate the cheap from the expensive gates and sort the latter according to a contribution-to-cost ratio
        cheap_gates = dict([gate for gate in self.circuit.items() if len(gate[0]) < 2])
        expensive_gates = dict([gate for gate in self.circuit.items() if len(gate[0]) >= 2])
        approximate_circuit = sorted(expensive_gates.items(), key = lambda gate: abs(gate[1]/(2*(len(gate[0])-1))))
        
        # Until the limit on the acceptable error is reached, omit gates with a small contribution-to-cost ratio
        current_error = 0
        while(len(approximate_circuit) > 0):
            error_contribution = abs(approximate_circuit[0][1])
            if error_contribution + current_error <= error_upper_bound:
                current_error += error_contribution
                approximate_circuit.pop(0)
            else:
                break

        # store the entire approximate circuit
        self.circuit = {**cheap_gates,**dict(approximate_circuit)}
        self.update_circuit_size()

    def evaluate_at(self, x):
            
            # simulate circuit for an input x
            final_rotation = 0
            for control_qubits, rotation_value in self.circuit.items():
                if control_qubits.issubset(x):
                    final_rotation += rotation_value
                        
            return final_rotation
        
    def evaluate_circuit_errors_for_all_inputs(self):
        
        accumulated_error = 0
        largest_error_so_far = 0
        at_input = {}
        
        # simulate every possible input to the circuit
        for input in self.possible_inputs():
            final_rotation = self.evaluate_at(input)
            
            #compute the corresponding classical input for comparison
            reference_input = 0
            for bit in input:
                reference_input += self.fractional_values[bit]
             
            #compute the largest absolute error that occured
            current_error = abs(final_rotation - self.function(reference_input))
            accumulated_error += current_error
            if current_error > largest_error_so_far:
                largest_error_so_far = current_error
                at_input = input

            average_error = accumulated_error / 2**self.register_size
        return average_error, largest_error_so_far, set(at_input)

    def show_accuracy(self):
        average_error, largest_error, position  = self.evaluate_circuit_errors_for_all_inputs()
        print("Average error: " + str(average_error))
        print("Largest error: " + str(largest_error) + " at " + str(position) + "\n")
    
    def show_circuit_size(self):
        print("Toffoli count: " + str(self.toffoli_count))
        print("Ancilla count: " + str(self.ancilla_count) + "\n")

        
# specify the size of the quantum register storing the argument x
n = 10

# define the fractional values of the argument x in the quantum register: Here, -0.5 <= x < 0.5 (equidistant over the interval)
fractional_values = [0.5**(i) for i in range(1,n+1)]
fractional_values[0] *= -1

# specify the function f in the rotation R(f(x))
f = lambda x: np.arcsin(x)

#compile the circuit
start = time.time()
c = RotationCircuit(fractional_values,f)
end = time.time()
print("Compilation time: " + str(end - start) + " seconds")

#print(c.circuit)
c.show_accuracy()
c.show_circuit_size()

c.approximate_up_to_an_error_of(1E-3)
#print(c.circuit)
c.show_accuracy()
c.show_circuit_size()
        

