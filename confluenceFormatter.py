from PythonConfluenceAPI import ConfluenceAPI
from bs4 import BeautifulSoup
from diff_match_patch import diff_match_patch
import re
import sys;
reload(sys);
sys.setdefaultencoding("utf8")

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
        self.responses = []

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
            # copy the response
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

            # parse the html
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
            self.tobeUpdated.append(responseCopy)
            self.responses.append(response)

    def getUpdated(self):
        return self.tobeUpdated

    def update(self):
        """
        Loop through updated items and POST to server
        :return:
        """
        for page in self.tobeUpdated:
            self.update_content_by_id(page, page['id'])

    def link(self, word, pageLoc, verify=False):
        """
        Links word to page
        :type word: string
        :param word:
        :param verify:
        :param pageLoc: (string) name of the page
        :return:
        """
        self.search(word).content(True)
        self.execute()
        self.linkModifier(word, pageLoc)
        if verify:
            dmp = diff_match_patch()
            html = """<!DOCTYPE html>
                    <html lang="en">
                    <head>
                    <meta charset="UTF-8">
                    <title>Title</title>
                    </head>
                    <body>"""
            for i in range(len(self.tobeUpdated)):
                html += "<h1>" + "Title: {}".format(self.tobeUpdated[i]['title']) + "</h1>"
                diffs = dmp.diff_main(self.responses[i]['body']['storage']['value'].decode(
                    'utf-8'), self.tobeUpdated[i]['body']['storage']['value'].decode(
                    'utf-8'))
                dmp.diff_cleanupSemantic(diffs)
                htmlSnippet = dmp.diff_prettyHtml(diffs)
                html += htmlSnippet

            html += "</body></html>"
            import datetime
            with open("link_" + word + "_to_" + pageLoc + str(datetime.datetime.now()) +
                              ".html", 'w') as file:
                file.write(html)
        else:
            self.update()
