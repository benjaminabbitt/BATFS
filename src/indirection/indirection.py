import sqlite3
import logging
import indirectionFile

from lib.singletonmixin import Singleton


class Indirection(Singleton):
    def isTag(self, tag):
        cur = self.con.cursor()
        cur.execute("SELECT count(tag_id) FROM tags WHERE tag_name = ?", (tag,));
        result = cur.fetchone()
        if (result[0] > 0):
            return True
        else:
            return False

    def getFile(self, expression, fileName):
        """
        Returns the File ID of file specified by fileName and expression.

        If the fileName and query do not represent an extant file, an IOError is raised.

        @return: File ID of file specified by query and fileName.
        """
        files = self._evaluateQuery(expression)

        if (files == None):
            #if we're here, the query didn't find anything at all
            raise IOError, "File Not Found."

        rVal = 0
        for file in files:
            if (fileName == file.getName()):
                rVal = file.getId()

        if not rVal:
            raise IOError, "File Not Found."
        return rVal

    def addFile(self, expression, fileName):
        """
        Adds a file to the database, returns the file id.
        """
        cur = self.con.cursor()
        cur.execute("""INSERT INTO files(file_id, file_name) VALUES(NULL, ?)""", (fileName,))
        id = cur.lastrowid
        self.con.commit()
        tags = self._getCanonicalName(expression)
        self.addTagsToFile(id, tags)
        return id, tags

    def getFiles(self, expression, canonical=False):
        """
        Returns a list of file names that match provided expression.
        If canonical==True, files are ONLY listed if all tags are matched.
        """
        files = self._evaluateQuery(expression)
        names = []
        if (files):
            for file in files:
                if (canonical):
                    fileTags = self.getTagsFromFile(expression, file.getName())
                    assertionTags = self._getCanonicalName(expression)
                    if (fileTags == assertionTags):
                        names.append(file.getName())
                else:
                    names.append(file.getName())

        return set(names)

    def retagFile(self, srcExpression, srcFileName, targetExpression, targetFileName):
        """
        Retags a file already managed by the utfs system.
        Evaluates srcExpression and srcFile into a unique id and then retags it and renames it to targetExpression and targetFileName.
        Emulates the "mv" command.
        """
        targetTags = self._getCanonicalName(targetExpression)
        srcTags = self._getCanonicalName(srcExpression)
        srcFile = self.getFile(srcExpression, srcFileName)

        tagsRm = None
        tagsAdd = None

        if (srcTags != targetTags):
            tagsAdd = set(targetTags).intersection(set(srcTags))
            tagsRm = set(srcTags).intersection(set(targetTags))

            self.rmTagsFromFile(srcFile, tagsRm)
            self.addTagsToFile(srcFile, tagsAdd)

        if (srcFileName != targetFileName):
            self._setFileName(srcFile, targetFileName)

        return tagsRm, tagsAdd


    def getTags(self, expression=[], guided=False):
        """
        Returns a list of tags.
        If guided is true, the list of tags will be pruned to only include relevant AND tags.
        If guided is false, the list will contain all tags.
        @return: A list of all tags
        """
        if (guided == False):
            cur = self.con.cursor()
            cur.execute("select tag_name from tags")
            tags = set([])
            for row in cur:
                tags.add(row[0])
        else:
            files = self._evaluateQuery(expression)
            tags = set([])
            for file in files:
                tags.update(self.getTagsFromFile(expression, file.getName()))

        #don't need the tags already in the expression
        exprTags = self._getCanonicalName(expression)
        if (exprTags):
            tags = tags - exprTags

        return tags

    def getTagsFromFile(self, expression, fileName):
        """
        Gets a list of all tags associated with the object specified by expression.
        """
        fid = self.getFile(expression, fileName)
        cur = self.con.cursor()
        cur.execute("SELECT tag_name FROM tags WHERE tag_id IN (SELECT tag_id FROM file_tag WHERE file_id = ?)",
                    (fid, ))
        tags = []
        for row in cur:
            tags.append(row[0])
        return set(tags)

    def rmTags(self, tags):
        """
        Removes a tag from the system.
        If doing so would orphan a file, the file is retagged to an orphan.
        """
        self.logger.info("Removing tags %s" % (tags))
        cur = self.con.cursor()
        for tag in tags:
            cur.execute("DELETE FROM file_tag WHERE tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)", (tag, ))
            cur.execute("DELETE FROM tags WHERE tag_name = ?", (tag, ))
        self.con.commit()
        #self._cleanupOrphans()


    def __init__(self, dataLocation=":memory:"):
        self.logger = logging.getLogger(str(self.__class__.__name__))
        #connect to db
        self.con = sqlite3.connect(dataLocation, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        #important change.  sqlite returns utf by default, which is incompatible with linux fs/fuse.  Return bytestrings with this change
        self.con.text_factory = str
        self.cur = self.con.cursor()

        self.con.execute("""CREATE TABLE IF NOT EXISTS files(
            file_id INTEGER PRIMARY KEY,
            file_name text)
            """)

        self.con.execute("""CREATE TABLE IF NOT EXISTS tags(
            tag_id INTEGER PRIMARY KEY,
            tag_name text)
            """)

        self.con.execute("""CREATE TABLE IF NOT EXISTS file_tag(
            join_id INTEGER PRIMARY KEY,
            file_id INTEGER REFERENCES files(file_id),
            tag_id INTEGER REFERENCES tags(tag_id))
            """)

        self.con.commit()


    def _getFilesFromTags(self, tagName):
        """
        @param tagName: the name of the tag for which we're retrieving all relevant files.
        @type tagName: String
        @return: A Set of tag IDs
        """
        cur = self.con.cursor()
        cur.execute(
            "SELECT file_tag.file_id, files.file_name FROM file_tag INNER JOIN files ON file_tag.file_id = files.file_id WHERE tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?)",
            (tagName,))
        tmp = cur.fetchall()
        fileSet = []
        #break the returned results back out into a traditional list.
        for item in tmp:
            fileSet.append(indirectionFile.IndirectionFile(item[0], item[1]))
        return set(fileSet)

    def addTagsToFile(self, fileId, tags):
        """
        Adds the input tag to the input file.  If the tag does not exist, it is created.  If the file does not exist, it is created.
        @param fileId: The file ID to which the tag is to be added.
        @type fileId: Integer
        @param tag: The tag names which are associated with the file name
        @type tag: List of Strings
        @return: The File ID for the (potentially created) file.
        """
        cur = self.con.cursor()
        self.logger.debug("Tags added: %s to file id: %s" % (tags, fileId))
        for tag in tags:
            cur.execute("""INSERT OR REPLACE INTO tags(tag_id, tag_name) VALUES(NULL, ?)""", (tag,))
            cur.execute(
                """INSERT INTO file_tag(file_id, tag_id) VALUES(?, (SELECT tag_id FROM tags WHERE tag_name = ?))""",
                (fileId, tag))
        self.con.commit()

    def addTags(self, tags):
        self.logger.debug("Adding Tags: %s" % (tags))
        cur = self.con.cursor()
        for tag in tags:
            cur.execute("""INSERT OR REPLACE INTO tags(tag_id, tag_name) VALUES(NULL, ?)""", (tag,))
        self.con.commit()

    def rmTagsFromFile(self, fileId, tags):
        """
        Removes the association between input tags and input file id.
        """
        cur = self.con.cursor()
        self.logger.debug("Tags removed: %s from file id: %s" % (tags, fileId))
        for tag in tags:
            cur.execute(
                "DELETE FROM file_tag WHERE tag_id = (SELECT tag_id FROM tags WHERE tag_name = ?) and file_id = ?",
                (tag, fileId))
        self.con.commit()
        #self._cleanupOrphans()

    def _evaluateQuery(self, expression):
        """
        Parse the provided expression and return a list of file names derived from it.
        @param expression: the expression we wish to evaluate

        @type expression: list of operators and operands, postfix notation
        @return a list of file names that match the expression
        """
        operators = ["AND", "OR", "NOT"]
        stack = []

        #run the pre-parser which replaces the tag names with their respective data sets.

        tmpExpression = []
        #first we preprocess and replace the tag names in the expressiohttp://docs.python.org/library/logging.htmln with the relevant sets.  In this instance, the stack is acting as a simple list.
        for element in expression:
            if (element in operators):
                tmpExpression.append(element)
            else:
                tmpExpression.append(self._getFilesFromTags(element))

        expression = tmpExpression

        #parse the expression
        for element in expression:
            #parse the explicit operators
            if (element in operators):
                try:
                    value1 = stack.pop()
                    value2 = stack.pop()
                except IndexError, e:
                    #used an operator without two data values on the stack
                    self.logger.error("Malformed Query")
                    return None

                if (element == "OR"):
                    stack.append(value1.union(value2))
                elif (element == "NOT"):
                    stack.append(value2.difference(value1))
                elif (element == "AND"):
                    stack.append(value1.intersection(value2))
            else:
                stack.append(element)

        #parse the implicit AND operators
        while (len(stack) > 1):
            value1 = stack.pop()
            value2 = stack.pop()
            stack.append(value1.intersection(value2))

        #at this point, the stack contains one item, a set of target file names.
        files = None

        try:
            files = stack[0]
            #do a frequency count of file names
            frqc = {}
            for file in files:
                if file.getName() in frqc:
                    frqc[file.getName()] += 1
                else:
                    frqc[file.getName()] = 1

            #if the occurance freqency is greater than 1, rename the file to avoid a collision.
            for file in files:
                if (frqc[file.getName()] > 1):
                    file.setName("%s(%s)" % (file.getName(), file.getId()))

        except IndexError, e:
            #no files were found that match query
            files = None

        return files


    def _getCanonicalName(self, expression):
        """

        Converts expression into a set of tags to which a file can be assigned
        It performs this operation by discarding tags from the expression which are of no value in an assertoin context (either by negation(not) or uncertainty(or))
        @param expression: Expresion to parse
        @type expression: List
        @return: List of tags
        """

        self.logger.info("Evaluating expression for canonical name.  Expression: %s" % (expression))
        operators = ["AND", "OR", "NOT"]
        stack = []

        for element in expression:
            #parse the explicit operators
            if (element in operators):
                try:
                    value1 = stack.pop()
                    value2 = stack.pop()
                except IndexError, e:
                    #used an operator without two data values on the stack
                    self.logger.error("Malformed Query")
                    return None

                if (element == "OR"):
                    #in the event of an OR, we don't care about either of the specified tags.
                    stack.append(None)
                elif (element == "NOT"):
                    stack.append(value2)
                elif (element == "AND"):
                    stack.append(value1)
                    stack.append(value2)
            else:
                stack.append(element)

        if None in stack:
            stack.remove(None)

        self.logger.info("%s is canonical form of %s" % (stack, expression))
        return set(stack)

    def _cleanupOrphans(self):
        """
        Finds file orphans (those with no tags) and adds the "orphan" tag to them
        """
        cur = self.con.cursor()
        orphans = cur.execute(
            "SELECT files.file_id FROM files LEFT OUTER JOIN file_tag ON files.file_id = file_tag.file_id AND file_tag.file_id = NULL")
        for item in orphans:
            self.addTagsToFile(item[0], ["orphan"])

    def _setFileName(self, fileId, fileName):
        cur = self.con.cursor()
        cur.execute("UPDATE files SET file_name = ? WHERE file_id = ?", (fileName, fileId))
        self.con.commit()


if __name__ == "__main__":
    ih = Indirection.getInstance()
    ih.addTags(["tag1"])
    ih.addTags(["tag2"])
    ih.addFile(["tag1"], "file")
    ih.addFile(["tag2"], "file2")
    print ih.getFiles(["tag1"])
    print ih.getTags("")

