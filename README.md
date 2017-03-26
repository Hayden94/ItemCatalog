# Udacity Full-Stack Nanodegree - Project 5 - Item Catalog

![alt front](http://i.imgur.com/2hqpupr.jpg)

This web app features a catalog created using Python, Google Dev Tools, HTML5, and CSS5. The app features a database and the web CRUD(Create Read Update Delete) functionality for said database. Once logged in using your Google Account, users have the ability to create their own categories and items. Users also have the ability to edit and delete any categories or items they have created.

## Getting Started

### Prerequisites
```
In order to get this project up and running, you will need Virtual Machine Sofware(Ex. Oracle VM Virtual Box), a linux command line(Git for windows users), and Vagrant

Simply, download and install Virtual Box, Git, and Vagrant.
```

Oracle's VM Virtual Box download can be found [here](https://www.virtualbox.org/wiki/Downloads).

Git can be found [here](https://git-scm.com/downloads).

Vagrant can be found [here](https://www.vagrantup.com/downloads.html)

## Deployment

**To run the project locally:**

* Open Virtual Box

* Open Git and cd into the directory that has catalog.py located inside of it.

![alt cd](http://i.imgur.com/F7xrJzp.jpg)

* Run the command vagrant up
    -This can be time consuming depending on the amount of software needed to be installed.

![alt appserver](http://i.imgur.com/uXRABXK.jpg)

    -If the command runs correctly, open up Virtual Box and you will see your Ubuntu VM running

![alt deploy](http://i.imgur.com/tINAhip.jpg)

* Run vagrant ssh into Git

![alt localhost](http://i.imgur.com/vLJkhGZ.jpg)

* Cd into /vagrant/catalog

![alt localhost](http://i.imgur.com/pi1vDQv.jpg)

* Run python populator.py in order to create the database and poplate it.

![alt localhost](http://i.imgur.com/ijPKj1A.jpg)

* Run python catalog.py to start the webserver

![alt localhost](http://i.imgur.com/YKV5pdU.jpg)

* Head over to localhost:8000 in order to view the blog

![alt localhost](http://i.imgur.com/bJWyzjB.jpg)

## Built With

* [Google Developer Tools](https://console.developers.google.com)
* [Python](https://www.python.org/)
* [HTML5](https://en.wikipedia.org/wiki/HTML5)
* [CSS3](https://en.wikipedia.org/wiki/Cascading_Style_Sheets)

## Authors

* **Hayden Oster** - *Initial work* - [Hayden94](https://github.com/Hayden94)
