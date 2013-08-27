lbaas-magic
===========

magical salty lbaas scripts

These tools are designed to facilitate the testing of both salt states and code for the libra (LBaaS) system.
The script will assist in:
-  the creation of a new salt-master vm
-  downloading the appropriate git salt state repos and setting up a basic pillar
-  bootstrapping the salt master for further action
-  deployment of libra environments
-  execution of the libra integration test suite

Setup:
The magic requires some preliminary work on your part
First of all, we expect that you have an HP Cloud account.
Second, we expect that you have created a keypair for use with the salt-master / test environments
Third, we expect you to have security group(s) created to allow the salt-master and libra infrastructure nodes to do their thing

We include a sample config file for guidance.
