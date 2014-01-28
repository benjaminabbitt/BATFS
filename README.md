#Introduction
Traditional file systems store data in a simple tree structure which is largely un-
changed since its creation in the 1970s. While this system is obviously adequate
for the majority of users, evolved file systems, those that are not rigidly pre-
planned and instead grow and mutate with use, need periodic maintenance to
keep organized. This organizational maintenance is made more difficult by the
fixed structure of the traditional hierarchical systems.


In addition to the above-mentioned problem, the type of files stored have also
changed substantially since the 1970s. Forty years ago, most files on a typical
system consisted of textual data and binary executables. Importantly, the text
files stored on these systems were query-able with simple command line tools
such as grep, awk, and cat. In modern times, typical file storage has moved
predominantly to binary files, be they archives, media files, or even text-containing
binary data (such as Microsoft Word or Excel data).


A key problem with this shift toward binary data is that text-searching tools
fail to function. BeOS, a now-defunct operating system attempted to address this
flaw with extensive integration of descriptors (tags) into its file system and file
browser utilities. Apple Spotlight allows a similar, but less pervasive, integration
of descriptors into the file system on the popular MacOS X platform. In more lim-
ited application, media players now frequently extract meta-data from an internal
library of files and store that meta-data in a searchable and browseable database.



##File System Query Language (FSQL)

To solve these problems, I propose the creation of a new method of file system
organization. Files will be stored using a set of tags and a file name, rather than a
path and their file name. The tags will appears as directories, but not bounded by
a tree structure. Tags will be loosely constrained and specified by the user.
The descriptors will be queried via a new query language, File System Query
Language (FSQL). FSQL is a postfix-based query language that will allow boolean
operations on sets of descriptors.




###FSQL Description

In evaluating FSQL Queries, all tags must first be converted into a set of files
associated with that tag. These sets are then evaluated.

In FSQL, expressions are evaluated in a postfix manner. A/B/AND is evalu-
ated as A∩B.

All operators are binary and evaluate the two sets of files immediately preced-
ing it.

In the special empty set case, all tags are returned and no files are returned.


###Application to the File System

FSQL Grammar is designed to be compatible with Linux/Unix file system gram-
mar. Tags appear as directories (permission changes are ignored), and files are
displayed normally.


###Name Collision Special Case

In the event that two files are named with the same file name, and the set of tags
associated with B is ⊂ the set of tags associated with A, and a FSQL expression is
4then devised such that expr. ⊆ B ⊂ A, a name collision will occur.

To resolve the name collision, I borrow an idea from Microsoft’s name colli-
sion avoidance routines in Windows, I add a parentheses and a number to the end
of the file name. In a deviation from Microsoft’s application, I do not assign the
lowest number that would not cause a collision, but instead assign the numerical
key assigned by the database to each file. This guarantees that the file name will
be unique, and provides consistency across the file system.

This file name (key) does not effect the name of the file within the storage file
system, and is just used to display and identify files within the query results.


###Recursion Special Case

Recursive deletion operations on this file system will result in the destruction of
the entire file system. It is for this reason that it is suggested that no recursive
operations be executed on the file system.

In an effort to provide some measure of insurance, the Trash Bin concept is
borrowed from Apple’s MacOS operating system, which places deleted files into
a file system buffer.

In my implementation, deleted files are placed into the reserved Trash tag.
When a file is placed into the Trash tag, all other tags associated with the file are
removed and archived in a file which is associated with the original file name. The
tags file is also placed within the Trash tag.
When a file with only the Trash tag is deleted, the file is unlinked from the
storage file system.

###Orphan Files

Files which have all associated tags removed are placed in a reserved Orphan tag.
This tag is removed automatically when a second tag is associated with the file.


##Examples

All examples, except when specified otherwise, are executed in Query Mode.
Given the set of picture files:
  File Name Tag     Tag
  A.jpg     Alice
  B.jpg     Bob
  C.jpg     Charlie
  AB.jpg    Alice   Bob

For example, this query will return everything with the tag Alice:
  
  $ls /Alice/

Yields the following results:

  a.jpg
  ab.jpg
  AND/
  Bob/
  Charlie/
  OR/
  NOT/

#####AND Support

Given the same set of files, the following is a query that will return everything with both the Alice and Bob tags.

  $ls /Alice/Bob/AND/

Yields:

  Alice/
  ab.jpg
  AND/
  Bob/
  Charlie/
  OR/
  NOT/

For the sake of brevity, AND operators can be omitted.

  $ls /Alice/Bob/

is equivalent to

  $ls /Alice/Bob/AND/

#####OR Support

Below is a query that will return everything that has either the Alice or the Bob
descriptors.

  $ls /Alice/Bob/OR/

Yields:

  a.jpg
  ab.jpg
  Alice/
  AND/
  b.jpg
  Bob/
  Charlie/
  OR/
  NOT/

#####NOT Support

NOT is also supported. Below is a query that will return everything with the tag Alice that does not also contain the tag Bob.

  $ls /Alice/Bob/NOT/

Yields
  
  a.jpg
  Alice/
  AND/
  Bob/
  Charlie/
  OR/
  NOT/

####Tag Assignment

Files can be added to the system simply by moving or copying them into a path
corresponding to the desired keywords. To copy and properly classify ab.jpg
with its appropriate tags Alice and Bob, one would simply copy it into the Alice
and Bob path, like so:

  $cp /previous/path/ab.jpg Alice/Bob/ab.jpg

OR and NOT operations will have their data sets discarded during tag assign-
ment operations. For example, the command:

  $cp /previous/path/foo.file /Alice/Bob/or/Charlie/Mike

Will result in the tags Charlie and Mike being assigned to foo.file. Alice
and Bob are both indefinite and are therefore discarded.
