import psycopg2

conn = psycopg2.connect("postgresql://moving_requests_user:BmkuL559dcrMjSsMCqBAUYAXNnFVEkBd@dpg-d0qta2re5dus739t66t0-a.virginia-postgres.render.com/moving_requests")
cur = conn.cursor()

# cur.execute("""
#     SELECT table_name 
#     FROM information_schema.tables 
#     WHERE table_schema = 'public' 
#     ORDER BY table_name;
# """)

cur.execute("""
    SELECT * from moving_requests;
""")

print(cur.fetchall())

# tables = cur.fetchall()
# for table in tables:
#     print(table[0])

conn.close()