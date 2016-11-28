from PythonConfluenceAPI import ConfluenceAPI
import copy

CQL_TEXT = "text~"

class ConfluenceFormatter(ConfluenceAPI):
    def __init__(self, username, password, uri_base):
        ConfluenceAPI.__init__(self, username, password, uri_base)
        self.search_words = []
        self.limit
        self.expands = []
        self.response = None
        self.tobeUpdated = []

    def search(self, word):
        """
        Append search word to list
        :param word: A string of the searched word
        :return: this instance for builder pattern
        """
        self.search_words.append(word)
        return self

    def limit(self, lim):
        """
        Update limit
        :param lim: An integer of returned responses
        :return: this instance for builder pattern
        """
        self.limit = lim
        return self

    def content(self, bool=True):
        """
        Get Page contents. Append "body.view" to CQL expansion query
        :param bool: A boolean to fetch body.view of JSON return
        :return: this instance for builder pattern
        """
        if bool:
            self.expands.append("body.storage,version")
        return self

    def __get_search_words(self):
        """
        Add search words into a single string and format it into CQL format
        :return: A string that is properly formatted
        """
        formatted = ' '.join('{0}'.format(w) for w in self.search_words)
        quote_formatted = CQL_TEXT + '"{0}"'.format(formatted)
        return quote_formatted

    def __get_expands(self):
        # Do preliminary work before returning string
        formatted = self.expands[0]
        return formatted

    def __get_limit(self):
        return self.limit

    def execute(self):
        self.response = self.search_content(self.__get_search_words(),
                                            expand=self.__get_expands(),
                                            limit=self.__get_limit())
        return self.response

    def modify(self):
        for response in self.response['results']:
            responseCopy = copy.deepcopy(response)
            responseCopy['version']['number'] += 1 # increment version number

            self.tobeUpdated.append(responseCopy)

    def getUpdated(self):
        return self.tobeUpdated


    # def
    #
    # def link(self, word, https):

