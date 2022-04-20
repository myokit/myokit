# Publication tests

The files in this directory are adaptations of examples distributed with publications.
They are included in the test to check for **syntax errors** or **changes in the API**.
This means the output they generate is not very important (although it can serve as a visual aid to find bugs).
More importantly, they should all run without errors, for at least a couple of major revisions after the version of Myokit the files were published with.

## Update 2017-11-23
Had to make some changes to DataLog, causing the 2nd parameter estimation example to fail.
Have adjusted the test file here, but the one published with the paper no longer works with versions >= 1.26.0
