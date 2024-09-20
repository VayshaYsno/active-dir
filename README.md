# This version is stabilized and migrated
## From OpenLDAP to LDAPS3.
Now all functions are working, and I can clearly understand EVERYTHING what I did in all process,
avoid 1 question. How did I passed SSL cert into it?
### I pulled cert in AD and into my own car also. And, it worked.

long time question was with `modifying`, and was resolved by [stackoverflow](https://stackoverflow.com/questions/38164544/unable-to-change-users-password-via-ldap3-python3) page.

#### Next step is to put all `methods` into `classes` and migrate to PostgreSQL. 
This part operating will develop in `dev` branch. This text and status, as MVP saved in `upg` branch.
This progress is also merged into `master`.