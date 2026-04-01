sql_for_create_user = '''
INSERT INTO users (first_name, last_name, email, password, phone, role, id)
VALUES
('user',
 'user', 
 'user@user.com', 
 '$2b$12$m08HRslO4jwlf04qRolf9eLsd.FLDHhjP5Dlen2WTQi6aJZkyeixa', 
 '+910000000000', 
 'USER',
 '7fa41ff5-d127-4d4a-b9b4-65f1b8b8b8b8'
 );
'''
#the default password is "Admin@123" we need to change it based on hashing algorithm
