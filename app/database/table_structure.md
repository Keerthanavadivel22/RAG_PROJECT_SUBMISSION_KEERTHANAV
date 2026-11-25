mysql> desc users;
+----------+--------------+------+-----+---------+----------------+
| Field    | Type         | Null | Key | Default | Extra          |
+----------+--------------+------+-----+---------+----------------+
| id       | int          | NO   | PRI | NULL    | auto_increment |
| username | varchar(100) | NO   |     | NULL    |                |
| email    | varchar(255) | NO   | UNI | NULL    |                |
| password | varchar(255) | NO   |     | NULL    |                |
+----------+--------------+------+-----+---------+----------------+


mysql> desc documents;
+-------------+--------------+------+-----+-------------------+-------------------+
| Field       | Type         | Null | Key | Default           | Extra             |
+-------------+--------------+------+-----+-------------------+-------------------+
| document_id | int          | NO   | PRI | NULL              | auto_increment    |
| file_name   | varchar(255) | NO   |     | NULL              |                   |
| file_path   | varchar(500) | NO   |     | NULL              |                   |
| uploaded_by | int          | NO   | MUL | NULL              |                   |
| uploaded_at | timestamp    | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+-------------+--------------+------+-----+-------------------+-------------------+


mysql> desc chunks;
+-------------+----------+------+-----+---------+----------------+
| Field       | Type     | Null | Key | Default | Extra          |
+-------------+----------+------+-----+---------+----------------+
| chunk_id    | int      | NO   | PRI | NULL    | auto_increment |
| document_id | int      | NO   | MUL | NULL    |                |
| chunk_text  | longtext | NO   |     | NULL    |                |
| chunk_index | int      | NO   |     | NULL    |                |
+-------------+----------+------+-----+---------+----------------+
4 rows in set (0.00 sec)

mysql> desc chat_messages;
+-------------+--------------------------+------+-----+-------------------+-------------------+
| Field       | Type                     | Null | Key | Default           | Extra             |
+-------------+--------------------------+------+-----+-------------------+-------------------+
| message_id  | int                      | NO   | PRI | NULL              | auto_increment    |
| user_id     | int                      | NO   | MUL | NULL              |                   |
| document_id | int                      | NO   | MUL | NULL              |                   |
| role        | enum('user','assistant') | NO   |     | NULL              |                   |
| content     | longtext                 | NO   |     | NULL              |                   |
| created_at  | timestamp                | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+-------------+--------------------------+------+-----+-------------------+-------------------+
6 rows in set (0.04 sec)
