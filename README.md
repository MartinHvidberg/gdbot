gdbot
=====

geo-data-bot


About
=====

This is a program that searches through geo-data data bases, hunting for errors and reporting or fixing them.
The definition of an error is stated in form of .gdbot files, that hold one error-definition per line, in a simple and structured form, i.e. each line in a .gdbot file is one rule (comment lines excepted), each rule specifies a single feature class, and describes a combiation of attribute values that is considered ilegal.

Why
===

Or maybe more relevant - why not use the Esri provided Data Reviwer?
The bold ansver is, because gdbot is simpler, faster and better.

We like Data Reviewer (D.R.), and use it frequently, but in some cases we find that gdbot better suites our needs.
gdbot have three advanteges over Data Reviewer.

Simpler: Creating a new rule in gdbot is literaly as easy as writing on line of text in an file. That is easier than going through the D.R. GUI. In particular if you have hundreds of rules that you want to create. We have occationally made Python scripts that generate large number of rules from various input, e.g. a spreadsheet. This allows us to quickly and easily check our data for a large number of errors, with an ease we could never get with D.R.

Faster: gdbot is a small Python script, it runs directely of your command-line prompt, without starting ArcMap. Though it has to start arcpy (which takes about 10 painfull seconds) gdbot still represents execution speed quite superiour to D.R.
As described above creating rules is also faster in gdbot, and the output is in plain text, and can optionally be send to your email address. Therefore, checking if the nightely run of gdbot revealed any errors, is as fast as opening your inbox.

Better: gdbot have the ability to find errors that can't (we think) be found with D.R. - therefore we risk to state that it's better. Of cause the exact same argument could be used to explain why D.R. is better, because D.R. can do many things that gdbot can't - but that's a minor detail :-)
gdbot run in several modes, including som that D.R. don't have. Modes, in this case, referes to the syntax of the .gdbot rule files. If you are unfamiliar with this syntax, please refere to the relevant files. Basically each line in a .gdbot file is one rule (comment lines excepted), each rule specifies a single feature class, and describes a combiation of attribute values that is not considered legal. ...
gdbot can fix errors ...

Shortcummings of gdbot
======================

gdbot can't check for topological errors, nor is there any present plans to impliment that.
As for now, gdbot can't check for errors that requires looking across multible feature classes, or even multible records in the same feature. gdbot is stricktely a record-by-record approach to error checking. More specifically, it uses an arcpy curser to walk the feature classes record-by-record, applying it's rule-based checks to each record in turn.

Environment
===========

The script is intented to work with Esri geo-data formats, and is made for ArcGIS 10.2 using Python.
The emmidiate purpose is to keep our data clean, but we hope others can see the use of this work.

/M
