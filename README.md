A survey of crypto library usage in Github Repositories. Created by Scott Griffy for Charles Winstead's CS586 Introduction to DBMS class at Portland State University, Fall 2018.

I created a scraper, database, and web interface that allows users to ask questions about the usage of different crypto libraries on github.
I ended up targeting 9 specific C crypto libraries due to the accuracy while querying them and their popularity:  
openssl - [info](https://www.openssl.org/)  
libsodium - [info](https://github.com/jedisct1/libsodium/blob/master/README.markdown)  
wolfssl - [info](https://www.wolfssl.com/)  
gnutls - [info](https://www.gnutls.org/)  
libtomcrypt - [info](https://github.com/libtom/libtomcrypt/blob/develop/README.md)  
mbedtls - [info](https://tls.mbed.org/)  
nettle - [info](https://www.lysator.liu.se/~nisse/nettle/)  
libgcrypt - [info](https://www.gnupg.org/software/libgcrypt/index.html)  
matrixssl - [info](https://github.com/matrixssl/matrixssl/blob/master/README.md)  
I used the Github API to populate my database, using the 'requests' package of python.

grad\_project\_er.py: used to generate the ER diagram and schema
scrape.py: used to gather data from Github and put it into the data
frontend.py: used to serve the data in the form of a web app

I've currently got a demo running at [http://cara.bid:8002/](http://cara.bid:8002/).

The proj\_sub\*.pdf files were submissions for this project for the class.
