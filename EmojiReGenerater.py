# encoding: utf-8
"""
A emoji filter regex generater.
This script can generater the regex for python to filter emoji from string.
The emoji rule data is from http://unicode.org/Public/emoji/5.0/emoji-data.txt
"""
import sys

LINE_WRAPER = ''
# LINE_WRAPER = '\n'


class Rule(object):
	def __init__(self, left, right):
		self.left = left 
		self.right = right 

class NarrowCode(object):
	def __init__(self, high, low):
		self.high = high
		self.low = low

class NarrowRule(object):
	def __init__(self, left, right):
		self.left = NarrowCode(*left)
		self.right = NarrowCode(*right)


class EmojiReGenerater(object):
	INPUT_FILE = './emoji-data.txt'

	NOT_EMOJI_LEFT = {0x0023, 0x002A, 0x0030}
	
	def __init__(self):
		self.left_rule_dict = {}
		self.right_rule_dict = {}
		self.res_rules = []
		self.narrow_res_rules = []
	
	def generate(self):
		with open(self.INPUT_FILE) as f:
			rules = [line for line in f.readlines() if self._input_rule_filter(line)]
		for rule in rules:
			res = rule[:14].strip().split('..')
			# print res
			if len(res) == 1:
				left, right = res[0], res[0]
			else:
				left, right = res[0], res[1]
			left, right = eval('0x%s' % left), eval('0x%s' % right)
			if left in self.NOT_EMOJI_LEFT:
				continue
			r = Rule(left, right)
			next_right = r.right + 1
			if next_right in self.left_rule_dict:
				next_right_rule = self.left_rule_dict[next_right]
				r.right = next_right_rule.right
				del self.right_rule_dict[next_right_rule.right]
				del self.left_rule_dict[next_right]
			before_left = r.left - 1
			if before_left in self.right_rule_dict:
				before_left_rule = self.right_rule_dict[before_left]
				r.left = before_left_rule.left
				del self.left_rule_dict[before_left_rule.left]
				del self.right_rule_dict[before_left]
			self.left_rule_dict[r.left] = r
			self.right_rule_dict[r.right] = r
		self._post_process()
	
	def _post_process(self):
		self.res_rules = []
		rule_keys = sorted(self.left_rule_dict.iterkeys())
		except_rule_idxs = set()
		for i in xrange(len(rule_keys)):
			if i in except_rule_idxs:
				continue
			ikey = rule_keys[i]
			cand_rule = self.left_rule_dict[ikey]
			for j in xrange(i+1, len(rule_keys)):
				jkey = rule_keys[j]
				rule = self.left_rule_dict[jkey]
				if cand_rule.left <= rule.left <= cand_rule.right:
					if rule.right > cand_rule.right:
						cand_rule.right = rule.right
					except_rule_idxs.add(j)
			self.res_rules.append(cand_rule)
	
	def print_wide_res(self):
		res = u'('
		for rule in self.res_rules:
			if rule.left == rule.right:
				res += '\U%08X|' % rule.left
			else:
				res += '[\U%08X-\U%08X]|' % (rule.left, rule.right)
			res += LINE_WRAPER
		if res[-1] == '|':
			res = res[:-1]
		res += u')+'
		print res

	def print_narrow_res(self):
		self._generate_narrow_res()
		res = u'('
		for nrule in self.narrow_res_rules:
			if nrule.left.high == 0x0 and nrule.right.high == 0x0:
				if nrule.left.low == nrule.right.low:
					res += '\u%04X|' % nrule.left.low
				else:
					res += '[\u%04X-\u%04X]|' % (nrule.left.low, nrule.right.low)
			else:
				if nrule.left.high == nrule.right.high:
					res += '\u%04X[\u%04X-\u%04X]|' % (nrule.left.high, nrule.left.low, nrule.right.low)
				else:
					low = nrule.left.low
					for high in xrange(nrule.left.high ,nrule.right.high):
						res += '\u%04X[\u%04X-\uDFFF]|' % (high, low)
						low = '\uDC00'
					res += '\u%04X[\uDC00-\u%04X]|' % (nrule.right.high, nrule.right.low)
			res += LINE_WRAPER
		if res[-1] == '|':
			res = res[:-1]
		res += u')+'
		print res
	
	def print_filter_char(self):
		def encode(value):
			str_val = '\\U%08X' % value
			return str_val.decode('unicode-escape').encode('utf-8')
		with open('filter_result.txt', 'w') as f:
			for rule in self.res_rules:
				if rule.left == rule.right:
					f.write(encode(rule.left))
				else:
					for i in xrange(rule.left, rule.right+1):
						f.write(encode(i))

	def _generate_narrow_res(self):
		self.narrow_res_rules = []
		for rule in self.res_rules:
			nrule = NarrowRule(Utils.to_utf16(rule.left), Utils.to_utf16(rule.right))
			self.narrow_res_rules.append(nrule)
			
	def _input_rule_filter(self, line):
		if len(line) >= 15 and line[14] == ';':
			return True
		return False


class Utils(object):
	@staticmethod
	def to_utf16(code):
		if sys.maxunicode == 65535:
			# UCS-2 python use decode to get narrow codec
			res = list(('\\U%08X' % code).decode('unicode-escape'))
			if len(res) == 1:
				return 0, ord(res[0])
			else:
				return ord(res[0]), ord(res[1])
		else:
			if code < 0x10000:
				return 0x0, code

			code = code - 0x10000
			hight = 0xD800 + ((code & (0b1111111111 << 10)) >> 10)
			low = 0xDC00 + (code & 0b1111111111)
			return hight, low


if __name__ == '__main__':
	res = Utils.to_utf16(0x10437)
	print '%04X %04X' % res
	generator = EmojiReGenerater()
	generator.generate()
	generator.print_wide_res()
	generator.print_narrow_res()
	generator.print_filter_char()
