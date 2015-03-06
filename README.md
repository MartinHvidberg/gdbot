gdbot
=====

geo-data-bot


About
=====

This is a program that searches through geo-data data bases, hunting for errors and reporting or fixing them.
The definition of an error is stated in form of .gdbot files, that hold one error-definition per line, in a simple and structured form, i.e. each line in a .gdbot file is one rule (comment lines excepted), each rule specifies a single feature class, and describes a combination of attribute values that is considered illegal.

Why
===

Or maybe more relevant - why not use the Esri provided Data Reviewer?
The bold answer is, because gdbot is simpler, faster and better.

We like Data Reviewer (D.R.), and use it frequently, but in some cases we find that gdbot better suites our needs.

gdbot have three advantages over Data Reviewer
==============================================

Simpler: Creating a new rule in gdbot is literally as easy as writing on line of text in a file. That is easier than going through the D.R. GUI. In particular if you have hundreds of rules that you want to create. We have occasionally made Python scripts that generate large number of rules from various input, e.g. a spreadsheet. This allows us to quickly and easily check our data for a large number of error-types, with an ease we could never get with D.R.

Faster: gdbot is a small Python script, it runs directly of your command-line prompt, without starting ArcMap. Though it has to start arcpy (which takes about 10 painful seconds) gdbot still represents execution speed quite superior to D.R.
As described above creating rules is also faster in gdbot, and the output is in plain text, and can optionally be send to your email address. Therefore, checking if the nightly run of gdbot revealed any errors, is as fast as looking in your in-box.

Better: gdbot have the ability to find errors that can't (we think) be found with D.R., and in addition to finding errors, gdbot can fix errors - therefore we risk to state that it's better. Of cause a similar argument could be used to explain why D.R. is better than gdbot, because D.R. can do many things that gdbot can't - but that's a minor detail :-)
gdbot run in several modes, including some that D.R. don't have. Modes, in this case, refers to the syntax of the .gdbot rule files. If you are unfamiliar with this syntax, please refer to the relevant files for details. Basically each line in a .gdbot file is one rule (comment lines excepted), each rule specifies a single feature class, and describes a combination of attribute values that is considered illegal.
The part that describes the 'illegal combination of attributes' is often-most specified in SQL. That we call SQL-mode, and is a frequently used mode. All you can do in SQL-mode can also be done in D.R. (we believe). Some fields allow only a limited number of values, to be valid. These fields typically have attribute-domains associated, but in any case, a gdbot rule can check that no illegal values is to be found. In this simple case D.R. can still do the same, with a domain-check. Yet more complex situations will allow a field to hold a string, which is a comma separated list of values, where the values are each to be one of a limited set of values. E.g. a colour field allows the values (1,2,3,...,9) each representing a colour. Imagine that multicoloured items are allowed, and that the string value "4,6" is a legal value. This can be checked by gdbot using its "List Of Valid Elements" mode (LOVE-mode), which uses a special non-SQL syntax to distinguish legal from illegal values. This can not be achieved in D.R. (as far as we know). 

gdbot can fix errors. In each rule line, in a .gdbot file, the user can specify an 'action'. The default action is to report the error in the output log. But gdbot also have a 'Fix' action. If you happen to know that all objects with colour=7, should in fact be colour=6, you can write a one-line .gdbot file that will both find and fix this little issue, across you entire data base - that can not be achieved with D.R. (as far as we know).

Additionally, gdbot is extendable. If you know a bit of Python, and because gdbot is open source, you can extend the code to look for other types of errors. This will only require that you think up a new 'mode' and implement it in the Python code, and then start writing .gdbot rules files to comply with the new syntax - it's much simpler than it sounds.

Shortcomings of gdbot
======================

gdbot can't check for topological errors, nor is there any present plans to implement that.

As for now, gdbot can't check for errors that requires looking across multiple feature classes, or even multiple records in the same feature class. gdbot is strictly limited to a record-by-record approach to error checking. More specifically, it uses an arcpy courser to walk the feature classes record-by-record, applying it's rule-based checks to each record in turn.

Environment
===========

The script is intended to work with Esri geo-data formats, and is made for ArcGIS 10.2 using Python 2.7.
The immediate purpose is to keep our data clean, but we hope others can see the use of this work.

/M
