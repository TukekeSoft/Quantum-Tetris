from werkzeug.exceptions import abort
import os
from flask import make_response, jsonify
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, BasicAer, execute
import math
from decimal import Decimal
import numpy

class Quantum():

	MAX_QUBITS = os.environ['MAX_QUBITS']
	machineName = os.environ['MACHINE_NAME']

	def __init__(self):
		pass

	# Code adapted for random number from https://blog.red-badger.com/2018/9/24/generate-true-random-numbers-with-a-quantum-computer
	def generateRandomNumber(self, maxInt):

		result = self.getRandNum(maxInt)

		error = None
		if result is None:
			error = "Error in fetching quantum result"

		if error is None:
			return jsonify(
				randomInt=result,
			)

		return abort(make_response(jsonify(error), 400))

	def createSuperposition(self):

		result = self.createPieces()

		error = None
		if result is None:
			error = "Error in creating superposition"

		if error is None:
			return jsonify(
				result=result,
			)

		return abort(make_response(jsonify(error), 400))

	def determineSuperposition(self, prob):

		result = self.findSuperposition(prob)

		error = None
		if result is None:
			error = "Error in determining superposition"

		if error is None:
			return jsonify(
				result=result,
			)

		return abort(make_response(jsonify(error), 400))

	def applyHGate(self, superposition):
		result = self.determineHProb(superposition)

		error = None
		if result is None:
			error = "Error in determining superposition"

		if error is None:
			return jsonify(
				result=result,
			)

		return abort(make_response(jsonify(error), 400))


	def flipGrid(self, grid):
		self.flipEntangledGrid(grid)

		error = None
		if grid is None:
			error = "Error in flipping grid"

		if error is None:
			return jsonify(
				result=grid,
			)

		return abort(make_response(jsonify(error), 400))

	def flipEntangledGrid(self, grid):
		for k in grid.keys():
			q = QuantumRegister(2)
			c = ClassicalRegister(1)
			qc = QuantumCircuit(q, c)

			# Uses entanglement to flip the bits of the grid
			if grid[k]['value'] == 1:
				qc.x(1)
			qc.x(0)
			qc.cx(0,1)
			qc.measure(0, 0)
			qc.measure(1, 0)

			simulator = BasicAer.get_backend(self.machineName)
			job_sim = execute(qc, backend = simulator, shots=1)
			sim_result = job_sim.result()

			try:
				if sim_result.get_counts(qc)['0'] == 1:
					grid[k]['value'] = 0
			except KeyError:
				grid[k]['value'] = 1


	def findSuperposition(self, piece1_prob):

		angle = numpy.arccos(math.sqrt(piece1_prob)) * 2

		q = QuantumRegister(1)
		c = ClassicalRegister(1)
		qc = QuantumCircuit(q, c)

		qc.rx(angle, 0)
		qc.measure(0, 0)

		simulator = BasicAer.get_backend(self.machineName)
		job_sim = execute(qc, backend = simulator, shots=1)
		sim_result = job_sim.result()

		try:
			sim_result.get_counts(qc)['0']
			return 0
		except KeyError:
			return 1

	def determineHProb(self, superposition):

		# Determines angle to adjust spin based wanted probability
		angle = numpy.arccos(math.sqrt(superposition['piece1']["prob"])) * 2

		q = QuantumRegister(1)
		c = ClassicalRegister(1)
		qc = QuantumCircuit(q, c)

		qc.rx(angle, 0)
		qc.rz(angle, 0)
		qc.h(0)

		simulator = BasicAer.get_backend("statevector_simulator")
		job_sim = execute(qc, backend = simulator, shots=1)
		result = job_sim.result().results[0].data.statevector[1]
		conjugate = numpy.conjugate(result)
		piece1Prob = Decimal(float(numpy.multiply(result,conjugate)))
		piece1ProbRounded = float(round(piece1Prob, 2))
		piece2Prob = Decimal(1 - piece1ProbRounded)
		piece2ProbRounded = float(round(piece2Prob, 2))


		return {
			"piece1": {
				"type": superposition['piece1']["type"],
				"prob": piece1ProbRounded
			},
			"piece2": {
				"type": superposition['piece2']["type"],
				"prob": piece2ProbRounded
			}
		}



	def createPieces(self):

		probability1 = self.random_int(100) / float(100)
		probability2 = 1 - probability1
		type1=self.random_int(6)
		type2=self.random_int(6)

		while type1==type2:
			type2=self.random_int(6)

		return {
			"piece1": {
				"type": type1,
				"prob": probability1
			},
			"piece2": {
				"type": type2,
				"prob": probability2
			}
		}


	def getRandNum(self, maxInt):
		result = self.random_int(self.nextPowerOf2(maxInt))
		while result > maxInt:
			result = self.random_int(self.nextPowerOf2(maxInt))
		return result

	def random_int(self, maxInt):
		bits = ''
		n_bits = self.numBits(maxInt - 1)
		register_sizes = self.getRegisterSizes(n_bits, int(self.MAX_QUBITS))

		for x in register_sizes:
			q = QuantumRegister(x)
			c = ClassicalRegister(x)
			qc = QuantumCircuit(q, c)

			qc.h(q)
			qc.measure(q, c)

			simulator = BasicAer.get_backend(self.machineName)
			job_sim = execute(qc, backend = simulator, shots=1)
			sim_result = job_sim.result()
			counts = sim_result.get_counts(qc)

			bits += self.bitFromCounts(counts)
		return int(bits, 2)

	def nextPowerOf2(self, n):
		return int(math.pow(2, math.ceil(math.log(n, 2))))

	def bitFromCounts(self, counts):
		return [k for k, v in counts.items() if v == 1][0]

	def numBits(self, n):
		return math.floor(math.log(n, 2)) + 1 if n != 0 else 1

	def getRegisterSizes(self, n, max_qubits):
		register_sizes = [max_qubits for i in range(int(n / max_qubits))]
		remainder = n % max_qubits
		return register_sizes if remainder == 0 else register_sizes + [remainder]
