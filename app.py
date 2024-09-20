from ldap3 import Server, Connection, ALL, NTLM
import ldap
import ldap3
from ldap3.core.exceptions import LDAPException, LDAPBindError
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import sessionmaker, declarative_base
import base64


ldap_password = ''                #'Q1w2e3r4t5'
ldap_server = 'ldaps://'       #'ldap://192.168.50.39'
search_base = 'dc=AD,dc=kusochek'           #'dc=nc,dc=local'
user_dn_prefix = 'cn='
user_dn_suffix = ',cn=Users,dc=AD,dc=kusochek'  #',cn=Users,dc=nc,dc=local'

output_file = "users.txt"

database = create_engine('mysql+pymysql://root:userer@127.0.0.1:3306/dbfile')
Baza = declarative_base()


class Insider(Baza):
    __tablename__ = 'ADUsers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    u_name = Column(String(100), nullable=False, unique=True)
    u_mail = Column(String(100), nullable=False, unique=True)

    @classmethod
    def get_unique(cls, u_name, u_mail):
        cache = session._unique_cache = getattr(session, '_unique_cache', {})
        key = (cls, u_name, u_mail)
        x = cache.get(key)
        if x is None:
            x = session.query(cls).filter_by(name=u_name, mail=u_mail).first()
            if x is None:
                x = cls(name=u_name, mail=u_mail)
                session.add(x)
            cache[key] = x
        return


Session = sessionmaker(bind=database)
session = Session()
Baza.metadata.create_all(database)


def insertDB_user(session, name, email):
    existing_user = session.query(Insider).filter_by(u_name=name,u_mail=email).first()
    if existing_user is None:
        user = Insider(u_name=name, u_mail=email)
        session.add(user)
        session.commit()
    else:
        print(f"User already existing: {name}")


def connect_ldap():
    try:
        server = Server(ldap_server, get_info=ALL)
        user = "10.11.128.128\\d.babii"
        password=ldap_password
        conn = Connection(server, user=user, password=password, authentication=NTLM, auto_bind=True)
        print("LDAPS Connection successfully granted", "\n")
        return conn
    except LDAPException as e:
        print(f"LDAPS connection error: {e}")
        return None


def disconnect_ldap(conn):
    conn.unbind()
    print("\n", "LDAP connection closed", "\n")


def push_db(session, users):
    for user in users:
        insertDB_user(session, user["name"], user['email'])
        session.close()


def push_file(conn):
    try:
        conn.search(search_base = 'dc=AD,dc=kusochek',
                    search_filter = '(objectcategory=person)',
                    attributes = ['givenName', 'name', 'userPrincipalName']
                    )
        if conn.entries:
            with open(output_file, 'a') as file:
                for entry in conn.entries:
                    if 'givenName' in entry and 'name' in entry and 'userPrincipalName' in entry:
                        name = entry['name']
                        email = entry['userPrincipalName']
                        if email:
                            file.write(f"name: {name}\n")
                            file.write(f"E-mail: {email}\n")
                            file.write("-----------------------------------\n")
    except LDAPException as e:
        print(f"LDAP connection error: {e}")


def get_users(conn):
    users = []
    try:
        conn.search(search_base = 'dc=AD,dc=kusochek',
                    search_filter = '(objectcategory=person)',
                    attributes = ['givenName', 'name', 'userPrincipalName']
                    )
        user_count = 0
        for entry in conn.entries:
                name = entry['name']
                email = entry['userPrincipalName']
                if email:
                    user_count+=1
                    users.append({'name': name, 'email': email})
                    print(f"{name}", "\t", end=" ")
                    print(f"{email}")
        print("Users available:",user_count)
    except LDAPException as e:
        print(f"LDAP connection error: {e}")
    return users


def get_all(conn):
    try:
        conn.search(search_base='dc=AD,dc=kusochek',
                    search_filter='(objectCategory=person)',
                    attributes='*'
                    )
        for entry in conn.entries:
            print(f'<-------DN: {entry.entry_dn}')
            attributes = entry.entry_attributes_as_dict
            for attr, value in attributes.items():
                print(f'{attr}:{value}')
            print('--------------------------------------- \n')
    except LDAPException as e:
        print(f"LDAP connection error: {e}")


def create_user(conn, name, email):
    try:
        tog=name+email
        new_entry = {
            'objectClass':[b'top',b'person', b'organizationalPerson', b'user'],
            'cn':name.encode('utf-8'),
            'givenName':name.encode('utf-8'),
            'displayName':name.encode('utf-8'),
            'sAMAccountName':name.encode('utf-8'),
            'userPrincipalName':tog.encode('utf-8'),
        }
        dn = user_dn_prefix + new_entry['cn'].decode('utf-8') + user_dn_suffix
        conn.add(dn,['top','person'], new_entry)
        print(f'New user "{name}" added successfully')
    except LDAPException as e:
        print(f"Error while creating: {e}")


def modifying(conn, user_cn, access):
    try:
        lv1 = access.encode('utf-16-le')
        lve2 = base64.b64encode(lv1).decode('utf-8')

        dn = user_dn_prefix + user_cn + user_dn_suffix

        uac = 66048 #544
        mod_list = {
           'userAccountControl': [(ldap.MOD_REPLACE, [str(uac).encode('utf-8')])],
        }
        conn.modify(dn,mod_list)
        conn.extend.microsoft.modify_password(dn, access)
        print("User modified successfully")
    except LDAPException as e:
        print(f"Error while modifying: {e}")


def delete_user(conn, user_cn):
    try:
        dn = user_dn_prefix + user_cn + user_dn_suffix
        conn.delete(dn)
        print(f'User "{user_cn}" deleted')
    except LDAPException as e:
        print(f"Error while deleting: {e}")


ldap_connection = connect_ldap()

# get_users(ldap_connection)   # WORKING - same 1
# get_all(ldap_connection)     # WORKING

# users = get_users(ldap_connection)   # WORKING - same 1
# push_db(session, users)        # WORKING

# push_file(ldap_connection)   # WORKING

# create_user(ldap_connection, name=input("Enter your login: "), email='@AD.kusochek') # WORKING
# delete_user(ldap_connection, user_cn=input("Kill: "))  # WORKING
# modifying(ldap_connection, user_cn=input('Enter login to modify:' ), access=input('Enter new password: '))  # WORKING

disconnect_ldap(ldap_connection)
