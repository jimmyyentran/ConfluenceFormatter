from PythonConfluenceAPI import ConfluenceAPI
from bs4 import BeautifulSoup
import re
import copy
import json


class ConfluenceFormatter(ConfluenceAPI):
    CQL_TEXT = "text~"
    LINK1 = '<ac:link><ri:page ri:content-title="'
    LINK2 = '"/><ac:plain-text-link-body><![CDATA['
    LINK3 = ']]></ac:plain-text-link-body></ac:link>'

    def __init__(self, username, password, uri_base):
        ConfluenceAPI.__init__(self, username, password, uri_base)
        self.search_words = []
        self.lim = 1
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
        self.lim = lim
        return self

    def content(self, bool=True):
        """
        Get Page contents. Append "body.storage,version" to CQL expansion query
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
        quote_formatted = self.CQL_TEXT + '"{0}"'.format(formatted)
        return quote_formatted

    # TODO Do preliminary work before returning string
    def __get_expands(self):
        formatted = self.expands[0]
        return formatted

    def __get_limit(self):
        return self.lim

    def execute(self):
        """
        Run the query and save it as an instance field
        :return: json object
        """
        self.response = self.search_content(self.__get_search_words(),
                                            expand=self.__get_expands(),
                                            limit=self.__get_limit())
        return self.response

    def linkModifier(self, searchStr, pageLoc):
        """
        Find a word and link it to the page location. Add to
        list of updated items
        :param searchStr: string to be linked
        :param pageLoc: string of the name of linked page
        :return:
        """
        for response in self.response['results']:
            responseCopy = copy.deepcopy(response)
            responseCopy['version']['number'] += 1  # increment version number
            # responseBody = responseCopy['body']['storage']['value']
            responseBody = responseCopy['body']['view']['value']
            bs = BeautifulSoup(responseBody)
            links = bs.findAll('ac:link')

            for link in links:
                # search pre-existing links
                linkedWord = re.findall('\[CDATA\[(.*?)\]\]', str(link))[0]

                if linkedWord is None:
                    break

                if searchStr == linkedWord:
                    firstChild = link.contents[0]
                    firstChild['ri:content-title'] = pageLoc

            matches = bs.findAll(text=re.compile(r'\b' + searchStr + r'\b'))

            for match in matches:
                # search and replace non-links
                substituted = re.sub(r'\b' + searchStr + r'\b',
                                     self.LINK1 + pageLoc + self.LINK2 +
                                     searchStr + self.LINK3, match)
                match.replaceWith(BeautifulSoup(substituted))

            # do replacement
            responseCopy['body']['view']['value'] = unicode(bs)

            self.tobeUpdated.append(responseCopy)

    def linkModifier2(self, searchStr, pageLoc):
        """
        Find a word and link it to the page location. Add to
        list of updated items
        :param searchStr: string to be linked
        :param pageLoc: string of the name of linked page
        :return:
        """
        for response in self.response['results']:
            responseCopy = {}
            responseCopy['id'] = response['id']
            responseCopy['type'] = response['type']
            responseCopy['title'] = response['title']
            responseCopy['body'] = {}
            responseCopy['body']['storage'] = {}
            responseCopy['body']['storage']['representation'] = response['body']['storage'][
                'representation']
            responseCopy['body']['storage']['value'] = response['body']['storage']['value']
            responseCopy['version'] = {}
            responseCopy['version']['number'] = response['version']['number'] + 1
            responseBody = responseCopy['body']['storage']['value']

            bs = BeautifulSoup(responseBody, "html.parser")
            matches = bs.findAll(text=re.compile(r'\b' + searchStr + r'\b'))

            # search and replace non-links
            for match in matches:

                # check if part of a link
                if match.parent.name == "ac:plain-text-link-body":
                    # is link
                    match.parent.previous_sibling['ri:content-title'] = pageLoc
                else:
                    # is not a link
                    substituted = re.sub(r'\b' + searchStr + r'\b',
                                         self.LINK1 + pageLoc + self.LINK2 +
                                         searchStr + self.LINK3, match)
                    match.replaceWith(BeautifulSoup(substituted, "html.parser"))

            # do replacement
            responseCopy['body']['storage']['value'] = bs.encode('utf-8')
            print "MY REQUEST"
            print "-------------------------------"
            print json.dumps(responseCopy, indent=4)
            print "-------------------------------"
            self.tobeUpdated.append(responseCopy)

    def getUpdated(self):
        return self.tobeUpdated

    def update(self):
        """
        Loop through updated items and POST to server
        :return:
        """
        for page in self.tobeUpdated:
            self.update_content_by_id(page, page['id'])

    def link(self, word, pageLoc):
        """
        Links word to page
        :param searchStr: string of the word needed to be linked
        :param pageLoc: (string) name of the page
        :return:
        """
        self.search(word).content(True)
        self.execute()
        self.linkModifier2(word, pageLoc)
        # self.update()
