# 
# The SHA-256 hash function. It is described in FIPS Publication 180.
# 
# Copyright (c) 2015 Project Nayuki. (MIT License)
# https://www.nayuki.io/page/cryptographic-primitives-in-plain-python
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
# - The above copyright notice and this permission notice shall be included in
#   all copies or substantial portions of the Software.
# - The Software is provided "as is", without warranty of any kind, express or
#   implied, including but not limited to the warranties of merchantability,
#   fitness for a particular purpose and noninfringement. In no event shall the
#   authors or copyright holders be liable for any claim, damages or other
#   liability, whether in an action of contract, tort or otherwise, arising from,
#   out of or in connection with the Software or the use or other dealings in the
#   Software.
# 

import cryptocommon


# ---- Public functions ----

# Computes the hash of the given bytelist message, returning a new 32-element bytelist.
def hash(message, printdebug=False):
	# Make a shallow copy of the list to prevent modifying the caller's list object
	assert type(message) == list
	msg = list(message)
	if printdebug: print("sha256.hash(message = {} bytes)".format(len(message)))
	
	# Append the termination bit (rounded up to a whole byte)
	msg.append(0x80)
	
	# Append padding bytes until message is exactly 8 bytes less than a whole block
	while (len(msg) + 8) % _BLOCK_SIZE != 0:
		msg.append(0x00)
	
	# Append the length of the original message in bits, as 8 bytes in big endian
	bitlength = len(message) * 8
	for i in reversed(range(8)):
		msg.append((bitlength >> (i * 8)) & 0xFF)
	
	# Initialize the hash state
	state = (0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
	         0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19)
	
	# Compress each block in the augmented message
	assert len(msg) % _BLOCK_SIZE == 0
	for i in range(len(msg) // _BLOCK_SIZE):
		block = tuple(msg[i * _BLOCK_SIZE : (i + 1) * _BLOCK_SIZE])
		if printdebug: print("    Block {} = {}".format(i, cryptocommon.bytelist_to_debugstr(block)))
		state = _compress(block, state, printdebug)
	
	# Serialize the final state as a bytelist in big endian
	result = []
	for x in state:
		for i in reversed(range(4)):
			result.append(int((x >> (i * 8)) & 0xFF))
	if printdebug: print("")
	return result


# ---- Private functions ----

# Requirement: All elements of block and state must be uint32.
def _compress(block, state, printdebug):
	# Check argument types and lengths
	assert type(block) == tuple and len(block) == _BLOCK_SIZE
	assert type(state) == tuple and len(state) == 8
	
	# Alias shorter names for readability
	mask32 = cryptocommon.UINT32_MASK
	rotr32 = cryptocommon.rotate_right_uint32
	
	# Pack block bytes into first part of schedule as uint32 in big endian
	schedule = [0] * 16
	for (i, b) in enumerate(block):
		assert 0 <= b <= 0xFF
		schedule[i // 4] |= b << ((3 - (i % 4)) * 8)
	
	# Extend the message schedule by blending previous values
	for i in range(len(schedule), len(_ROUND_CONSTANTS)):
		x = schedule[i - 15]
		y = schedule[i -  2]
		smallsigma0 = rotr32(x,  7) ^ rotr32(x, 18) ^ (x >>  3)
		smallsigma1 = rotr32(y, 17) ^ rotr32(y, 19) ^ (y >> 10)
		temp = (schedule[i - 16] + schedule[i - 7] + smallsigma0 + smallsigma1) & mask32
		schedule.append(temp)
	
	# Unpack state into variables; each one is a uint32
	a, b, c, d, e, f, g, h = state
	
	# Perform 64 rounds of hashing
	for i in range(len(schedule)):
		# Perform the round calculation
		if printdebug: print("        Round {:2d}: a={:08X}, b={:08X}, c={:08X}, d={:08X}, e={:08X}, f={:08X}, g={:08X}, h={:08X}".format(i, a, b, c, d, e, f, g, h))
		bigsigma0 = rotr32(a, 2) ^ rotr32(a, 13) ^ rotr32(a, 22)
		bigsigma1 = rotr32(e, 6) ^ rotr32(e, 11) ^ rotr32(e, 25)
		choose = (e & f) ^ (~e & g)
		majority = (a & b) ^ (a & c) ^ (b & c)
		t1 = (h + bigsigma1 + choose + schedule[i] + _ROUND_CONSTANTS[i]) & mask32
		t2 = (bigsigma0 + majority) & mask32
		h = g
		g = f
		f = e
		e = (d + t1) & mask32
		d = c
		c = b
		b = a
		a = (t1 + t2) & mask32
	
	# Return new state as a tuple
	return (
		(state[0] + a) & mask32,
		(state[1] + b) & mask32,
		(state[2] + c) & mask32,
		(state[3] + d) & mask32,
		(state[4] + e) & mask32,
		(state[5] + f) & mask32,
		(state[6] + g) & mask32,
		(state[7] + h) & mask32)


# ---- Numerical constants/tables ----

_BLOCK_SIZE = 64  # In bytes

_ROUND_CONSTANTS = [  # 64 elements of uint32
	0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5,
	0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
	0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3,
	0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
	0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC,
	0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
	0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7,
	0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
	0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13,
	0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
	0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3,
	0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
	0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5,
	0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
	0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208,
	0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
]
