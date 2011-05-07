import abc
class ReviewModule:
	__metaclass__ = abc.ABCMeta
	@abc.abstractmethod
	def get_score(self, query):
		pass
