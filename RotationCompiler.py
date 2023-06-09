import numpy as np
from itertools import combinations
import time

class RotationCircuit():
    
    def __init__(self, bit_weigts, function):
        
        self.bit_weigts = bit_weigts.copy()
        self.register_size = len(self.bit_weigts)
        self.function = function

        self.needs_recompilation = False
        
        self.compile()

    def compile(self):

        # a list of dictionaries, where the k-th dictionary will store the k-fold controlled rotation gates
        circuit = [dict() for _ in range(self.register_size+1)]
        
        # compile a quantum lookup-table for the given function
        for input in self.possible_inputs():
            input_value = self.compute_value_of(input)
            circuit[len(input)][input] = self.function(input_value)
        
        # transform the structure the lookup-table such that the contribution of a single rotation gate to the final result is distributed among many other rotation gates
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

    # generator for iterating over all possible inputs {}, {0}, {1},..., {0,1,...,n-1} for the quantum algorithm. In case a function is used 
    # that is not defined for any of these values, this generator function could be modified accordingly. 
    def possible_inputs(self):
        input_bits = set([index for index in range(0,self.register_size)])
        for hamming_weight in range(0,self.register_size+1):
            for input in combinations(input_bits, hamming_weight):
                yield frozenset(input)
    
    def update_circuit_size(self):
        self.toffoli_count = np.sum([max(2*(len(control_qubits)-1),0) for control_qubits in self.circuit.keys()])
        self.ancilla_count = max(np.max([len(control_qubits) for control_qubits in self.circuit.keys()])-1,0)

    def get_circuit(self):
        return self.circuit

    def approximate_up_to_toffoli_count_of(self, maximum_toffoli_count):

        if self.needs_recompilation:
            self.compile()
        
        # seperate the cheap from the expensive gates and sort the latter according to a contribution-to-cost ratio
        cheap_gates = dict([gate for gate in self.circuit.items() if len(gate[0]) < 2])
        expensive_gates = dict([gate for gate in self.circuit.items() if len(gate[0]) >= 2])
        approximate_circuit = sorted(expensive_gates.items(), key = lambda gate: abs(gate[1]/(2*(len(gate[0])-1))), reverse=True)
        
        # Until the limit on the acceptable error is reached, omit gates with a small contribution-to-cost ratio
        current_toffoli_count = 0
        position = 0
        while(position < len(approximate_circuit)):
            current_gate_toffoli_count = 2*(len(approximate_circuit[position][0])-1)
            if current_toffoli_count + current_gate_toffoli_count > maximum_toffoli_count:
                break
            else:
                current_toffoli_count += current_gate_toffoli_count
                position += 1
        
        approximate_circuit = approximate_circuit[:position]

        # store the entire approximate circuit
        self.circuit = {**cheap_gates,**dict(approximate_circuit)}
        self.update_circuit_size()
        self.needs_recompilation = True

    def approximate_up_to_an_error_of(self, error_upper_bound):

        if self.needs_recompilation:
            self.compile()
        
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
        self.needs_recompilation = True

    def evaluate_at(self, x):
            
        # simulate circuit for an input x
        final_rotation = 0
        for control_qubits, rotation_value in self.circuit.items():
            if control_qubits.issubset(x):
                final_rotation += rotation_value
                    
        return final_rotation
        
    def compute_error_statistics(self):
        
        accumulated_error = 0
        largest_error_so_far = 0
        at_input = {}

        number_of_inputs = 0
        
        # simulate every possible input to the circuit
        for input in self.possible_inputs():
            final_rotation = self.evaluate_at(input)
            
            #compute the corresponding classical input for comparison
            reference_input = self.compute_value_of(input)
             
            #compute the largest absolute error that occured
            current_error = abs(final_rotation - self.function(reference_input))
            accumulated_error += current_error
            if current_error > largest_error_so_far:
                largest_error_so_far = current_error
                at_input = input

            number_of_inputs += 1

        average_error = accumulated_error / number_of_inputs
        return average_error, largest_error_so_far, set(at_input)

    def compute_value_of(self, input):
        input_value = 0
        for bit in input:
            input_value += self.bit_weigts[bit]
        return input_value

    def show_accuracy(self):
        average_error, largest_error, position  = self.compute_error_statistics()

        position_value = self.compute_value_of(position)

        print("\tAverage error: " + str(average_error))
        print("\tLargest error: " + str(largest_error) + " at " + str(position) + " = " + str(position_value) + "\n")
    
    def show_circuit_size(self):
        print("\tToffoli count: " + str(self.toffoli_count))
        print("\tAncilla count: " + str(self.ancilla_count) + "\n")

    def show_circuit(self):
        column_width = 2 + 3*(self.ancilla_count+1)-2
        for control_qubits, rotation_value in self.circuit.items():
            if len(control_qubits) == 0:
                printed_characters = 2
                for _ in range(column_width - printed_characters):
                    print(" ", end='') 
                print("{}", end='')
                print("\t" + str(rotation_value))
            else :
                printed_characters = 2 + 3*len(control_qubits)- 2
                for _ in range(column_width - printed_characters):
                    print(" ", end='') 
                print(set(control_qubits), end='')
                print("\t" + str(rotation_value))
    

        
# specify the size of the quantum register storing the argument x
n = 8

# define the fractional values of the argument x in the quantum register: Here, -0.5 <= x < 0.5 (equidistant over the interval)
# bit_weights = [-0.5, 0.25, 0.125, .., 2^{-n}]
bit_weigts = [0.5**(i) for i in range(1,n+1)]
bit_weigts[0] *= -1

# specify the function f in the rotation R(f(x))
f = lambda x: np.arcsin(x)

#compile the circuit
start = time.time()
c = RotationCircuit(bit_weigts,f)
end = time.time()
print("Compilation time: " + str(end - start) + " seconds\n")

print("Exact circuit:")
c.show_accuracy()
c.show_circuit_size()
# c.show_circuit()

print("Approximate circuit 1:")
c.approximate_up_to_an_error_of(1E-4)
c.show_accuracy()
c.show_circuit_size()
# c.show_circuit()

print("Approximate circuit 2:")
c.approximate_up_to_toffoli_count_of(500)
c.show_accuracy()
c.show_circuit_size()
# c.show_circuit()

        



