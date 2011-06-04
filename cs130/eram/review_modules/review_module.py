import abc
class ReviewModule:
    __metaclass__ = abc.ABCMeta
    @abc.abstractmethod
    # Should return a tuple containing the review score and the number of reviews
    def get_score(self, query, query_type):
        pass

    @abc.abstractmethod
    # Should return the name of the review module. Useful for displaying the 
    # score breakdown by review modules.
    def get_name(self):
        pass
