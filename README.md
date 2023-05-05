# quantum-rotation-compiler

A Python program for compiling approximate lookup-tables to perform arbitrary function rotations on quantum computers.

## Usage

The code implements the `RotationCompiler` class. The constructor takes two arguments:
- a list `bit_weights` that stores the bit weights of the argument quantum register
- a function `function` to implement the corresponding function rotation.

Most of the computational work happens in the constructor, which compiles a lookup-table for the given function and transforms its structure such that the circuit can be made approximate with one of the following methods:

- `approximate_up_to_toffoli_count_of(maximum_toffoli_count)` 
- `approximate_up_to_an_error_of(self, error_upper_bound)`

The first method reduces the circuit depth of the lookup-table until its Toffoli count is smaller or equal `maximum_toffoli_count`. The second method reduces the circuit depth as much as possible as long as the introduced error is guaranteed to be smaller or equal to `error_upper_bound`.
The methods

- `show_accuracy()`
- `show_circuit_size()`
- `show_circuit()`

can be used in order to print out information about the resulting quantum circuit.

## Important notes
The algorithm scales exponentially in the size of the argument register. Therefore, it is advised to choose the length of `bit_weights` smaller than 16. In addition, this version of the program evaluates the function on every value that can be represented by a register with the given bit weights. Consequently, `function` should be chosen such that it is defined on any such value. 