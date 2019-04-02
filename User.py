from flask_login import UserMixin
from flask import g


class User(UserMixin):
    def __init__(self, email='', password='', name=''):
        UserMixin.__init__(self)
        self.email = email
        self.name = name
        self.password = password
        self.valid = False
        self.id = ''  # Extra id field for Flask-login requirement

    # @This Function verify whether a user is recorded
    def user_verify(self, user_type):
        eid = self.email
        code = self.password
        if eid.strip() == '':
            return
        if code.strip() == '':
            return
        if user_type == 'user':
            query = 'select * from usr where email like %s'
        elif user_type == 'admin':
            query = 'select * from admin where account like %s'
        else:
            raise ValueError('Invalid user type!')
        cursor = g.conn.execute(query, (eid, ))
        for row in cursor:
            key = str(row.password)
            if key.strip() == code.strip():
                self.name = str(row.name)
                self.email = eid
                self.id = eid
                self.valid = True
            break

    # @This function insert a new user into database
    def insert_new_user(self):
        try:
            query = '''
            insert into usr (email,name,password)
            values (%s,%s,%s)
            '''
            if self.email.strip() == '' or self.name.strip() == '' or self.name.strip() == '':
                return
            g.conn.execute(query, (self.email, self.name, self.password))
            self.valid = True
            if self.valid:
                self.id = self.email
        except:
            print('invalid user')

    '''
    Rewrite def in order to get things work
    '''
    def is_authenticated(self):
        if self.valid:
            return True
        return False

    def is_active(self):
        return True

    def get_id(self):
        return self.id
