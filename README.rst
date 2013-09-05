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
  - First of all, we expect that you have an HP Cloud account.
  - Second, we expect that you have created a keypair for use with the salt-master / test environments
  - Third, we expect you to have security group(s) created to allow the salt-master and libra infrastructure nodes to do their thing
  - Fourth, that you have fabric, pyyaml, and python-novaclient installed

We include a sample config file for guidance.

To run:

  - create saltmagic.cfg with the values filled out
  - call the program: python saltmagic.py --verbose

TODO:
  - more cleanup (allow the user to hit a flag that will go in and clean up created vm's + the saltmaster once they are done
  - more toggles
    - allow for specification of states repo
    - allow for specification of libra repo / ppa (?)
    - more switches in salt-states
    - clean this up
